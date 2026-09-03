import Map "mo:core/Map";
import Nat "mo:core/Nat";
import Principal "mo:core/Principal";
import Iter "mo:core/Iter";
import Array "mo:core/Array";
import Order "mo:core/Order";
import Runtime "mo:core/Runtime";
import Admin "mo:thebes-lib/Admin";
import MemphisAuth "mo:thebes-lib/MemphisAuth";
import Hex "Hex";
import Poll "Poll";

// TEMPO — the on-chain half of the tempo storefront example.
//
// The property this example proves: A RECOUNTABLE POLL. One boundary identity
// holds one standing vote (a revote replaces, never adds), so
//     sum(per-candidate tallies) == number of distinct voters
// and ANYONE can recompute that equality at ANY time via `recountView` —
// there are no counters to trust, only the votes map itself.
//
// Admin authority is NOT the transport sender: every admin method takes an
// origin-scoped Memphis session token, verifies it on-chain (MemphisAuth),
// and keys authority on the derived per-app principal. The passkey gate is
// load-bearing, not cosmetic.
persistent actor Tempo {

  // ── Catalogue ─────────────────────────────────────────────────────────────

  type Stock = { #stocked; #low; #out };

  type Sku = {
    id : Nat;
    name : Text;
    desc : Text;
    var pricePiastres : Nat; // EGP has 100 piastres: 20000 == EGP 200
    unit : Text;
    tag : Text;
    featured : Bool;
    var stock : Stock;
    sortOrder : Nat;
  };

  type Stockist = {
    id : Nat;
    var city : Text;
    var meta : Text;
    var spots : Nat;
    var lonMilli : Nat; // longitude x1000 (Egypt is all-positive)
    var latMilli : Nat;
  };

  let skus : Map.Map<Nat, Sku> = do {
    let m = Map.empty<Nat, Sku>();
    Map.add(m, Nat.compare, 1, { id = 1; name = "4-Pack"; desc = "A short stack of one flavour. The easy way to find your pace."; var pricePiastres = 20000; unit = "/ 4 cans"; tag = ""; featured = false; var stock = (#stocked : Stock); sortOrder = 1 });
    Map.add(m, Nat.compare, 2, { id = 2; name = "12-Case"; desc = "The training case. One flavour, twelve cans, best value per pour."; var pricePiastres = 54000; unit = "/ 12 cans"; tag = "Most popular"; featured = true; var stock = (#stocked : Stock); sortOrder = 2 });
    Map.add(m, Nat.compare, 3, { id = 3; name = "Variety Case"; desc = "Four of each — Citrus Strike, Arctic Berry, Lime Charge. Meet all three."; var pricePiastres = 56000; unit = "/ 12 cans"; tag = ""; featured = false; var stock = (#stocked : Stock); sortOrder = 3 });
    m;
  };

  let stockists : Map.Map<Nat, Stockist> = do {
    let m = Map.empty<Nat, Stockist>();
    Map.add(m, Nat.compare, 1, { id = 1; var city = "Cairo"; var meta = "Cafés, gyms & bike shops from Zamalek to New Cairo"; var spots = 38; var lonMilli = 31240; var latMilli = 30050 });
    Map.add(m, Nat.compare, 2, { id = 2; var city = "Alexandria"; var meta = "Run clubs & cafés along the Corniche"; var spots = 21; var lonMilli = 29920; var latMilli = 31200 });
    Map.add(m, Nat.compare, 3, { id = 3; var city = "El Gouna"; var meta = "The tri club, marina cafés & kite beaches"; var spots = 17; var lonMilli = 33680; var latMilli = 27390 });
    m;
  };
  var nextStockistId : Nat = 4;

  // ── Poll ──────────────────────────────────────────────────────────────────

  let poll : Poll.State = Poll.new([
    ("Mango Surge", "Alphonso mango, a squeeze of lime, the same 380mg of Sinai salt."),
    ("Pomegranate Rush", "Sharp Aswan pomegranate over the classic electrolyte base."),
    ("Mint Lime", "Fresh mint and double lime — the shandy of sports drinks."),
    ("Tamarind Volt", "Tamr hindi, carbonated. The one your grandmother would recognise."),
  ]);

  // ── Auth ──────────────────────────────────────────────────────────────────

  let admin : Admin.State = Admin.init();
  let gate : MemphisAuth.State = MemphisAuth.initFromCid(921, "thebes-example-tempo", 1);
  // The web origin this site is served from. Byte-exact — Memphis compares it
  // against the origin the token was minted for. Deliberately NOT state.
  let AUDIENCE : Text = "https://memphis.mercaturaforum.com";

  /// Verify an origin-scoped session token and hand back the caller's stable
  /// per-app principal. Every admin method funnels through here.
  func verified(tokenHex : Text) : async* ?Principal {
    switch (Hex.toBlob(tokenHex)) {
      case null { null };
      case (?token) {
        switch (await* MemphisAuth.verifyWithAudience(gate, token, AUDIENCE)) {
          case (#ok(id)) { ?id.principal };
          case (#err(_)) { null };
        };
      };
    };
  };

  func requireAdminSession(tokenHex : Text) : async* Principal {
    switch (await* verified(tokenHex)) {
      case null { Runtime.trap("session not verified") };
      case (?p) {
        Admin.requireNotPaused(admin);
        Admin.requireAdmin(admin, p);
        p;
      };
    };
  };

  // ── Public queries (flat records — the SDK runtime decoder's shape) ──────

  type SkuView = { id : Nat; name : Text; desc : Text; pricePiastres : Nat; unit : Text; tag : Text; featured : Bool; stock : Text; sortOrder : Nat };
  type StockistView = { id : Nat; city : Text; meta : Text; spots : Nat; lonMilli : Nat; latMilli : Nat };
  type CandidateRow = { id : Nat; name : Text; blurb : Text; tally : Nat; open : Bool; totalVotes : Nat };
  type RecountRow = { candidateId : Nat; tally : Nat; distinctVoters : Nat; sumTallies : Nat; holds : Bool };

  func stockText(s : Stock) : Text {
    switch (s) { case (#stocked) "in"; case (#low) "low"; case (#out) "out" };
  };

  public query func skusView() : async [SkuView] {
    let out = Iter.map<Sku, SkuView>(Map.values(skus), func(s) {
      { id = s.id; name = s.name; desc = s.desc; pricePiastres = s.pricePiastres; unit = s.unit; tag = s.tag; featured = s.featured; stock = stockText(s.stock); sortOrder = s.sortOrder };
    });
    Array.sort<SkuView>(Iter.toArray(out), func(a, b) : Order.Order { Nat.compare(a.sortOrder, b.sortOrder) });
  };

  public query func stockistsView() : async [StockistView] {
    Iter.toArray(Iter.map<Stockist, StockistView>(Map.values(stockists), func(s) {
      { id = s.id; city = s.city; meta = s.meta; spots = s.spots; lonMilli = s.lonMilli; latMilli = s.latMilli };
    }));
  };

  public query func pollView() : async [CandidateRow] {
    let total = Poll.totalVotes(poll);
    Iter.toArray(Iter.map<Poll.Candidate, CandidateRow>(Map.values(poll.candidates), func(c) {
      { id = c.id; name = c.name; blurb = c.blurb; tally = Poll.tally(poll, c.id); open = poll.open; totalVotes = total };
    }));
  };

  public query func recountView() : async [RecountRow] {
    let distinct = Poll.totalVotes(poll);
    let sum = Poll.sumTallies(poll);
    let holds = Poll.recountHolds(poll);
    Iter.toArray(Iter.map<Poll.Candidate, RecountRow>(Map.values(poll.candidates), func(c) {
      { candidateId = c.id; tally = Poll.tally(poll, c.id); distinctVoters = distinct; sumTallies = sum; holds };
    }));
  };

  public shared query (msg) func myVoteView() : async [{ candidateId : Nat }] {
    switch (Poll.myVote(poll, msg.caller)) {
      case null { [] };
      case (?id) { [{ candidateId = id }] };
    };
  };

  public query func hasOwner() : async Bool { Admin.getOwner(admin) != null };

  // ── Public write: the vote (transport-sender keyed, deliberately) ────────

  public shared (msg) func castVote(candidateId : Nat) : async Bool {
    Poll.cast(poll, msg.caller, candidateId);
  };

  // ── Admin surface (Memphis-verified, principal = derived per-app id) ─────

  public func checkAdmin(tokenHex : Text) : async Bool {
    switch (await* verified(tokenHex)) {
      case null { false };
      case (?p) { Admin.isAdmin(admin, p) };
    };
  };

  /// First VERIFIED Memphis identity claims ownership — an unverified or
  /// anonymous caller can never own the contract.
  public func claimOwner(tokenHex : Text) : async Bool {
    switch (await* verified(tokenHex)) {
      case null { false };
      case (?p) { Admin.claimOwner(admin, p) };
    };
  };

  public func setSkuPrice(tokenHex : Text, id : Nat, pricePiastres : Nat) : async Bool {
    ignore await* requireAdminSession(tokenHex);
    switch (Map.get(skus, Nat.compare, id)) {
      case null { false };
      case (?s) { s.pricePiastres := pricePiastres; true };
    };
  };

  public func setSkuStock(tokenHex : Text, id : Nat, stock : Text) : async Bool {
    ignore await* requireAdminSession(tokenHex);
    let v = switch (stock) {
      case ("in") #stocked; case ("low") #low; case ("out") #out;
      case (_) { return false };
    };
    switch (Map.get(skus, Nat.compare, id)) {
      case null { false };
      case (?s) { s.stock := v; true };
    };
  };

  public func upsertStockist(tokenHex : Text, id : Nat, city : Text, meta : Text, spots : Nat, lonMilli : Nat, latMilli : Nat) : async Bool {
    ignore await* requireAdminSession(tokenHex);
    if (id == 0) {
      let nid = nextStockistId;
      nextStockistId += 1;
      Map.add(stockists, Nat.compare, nid, { id = nid; var city = city; var meta = meta; var spots = spots; var lonMilli = lonMilli; var latMilli = latMilli });
      return true;
    };
    switch (Map.get(stockists, Nat.compare, id)) {
      case null { false };
      case (?s) {
        s.city := city; s.meta := meta; s.spots := spots;
        s.lonMilli := lonMilli; s.latMilli := latMilli;
        true;
      };
    };
  };

  public func setPollOpen(tokenHex : Text, open : Bool) : async Bool {
    ignore await* requireAdminSession(tokenHex);
    poll.open := open;
    true;
  };

  public func addCandidate(tokenHex : Text, name : Text, blurb : Text) : async Bool {
    ignore await* requireAdminSession(tokenHex);
    ignore Poll.addCandidate(poll, name, blurb);
    true;
  };

  /// The caller's derived per-app principal, in text — the panel shows it so
  /// an owner can add another admin by principal. "" when unverified.
  public func whoAmI(tokenHex : Text) : async Text {
    switch (await* verified(tokenHex)) {
      case null { "" };
      case (?p) { Principal.toText(p) };
    };
  };

  // Owner/admin management — each takes the OTHER party's derived principal in
  // text form (as shown by whoAmI in their own panel).
  public func addAdmin(tokenHex : Text, whoText : Text) : async Bool {
    switch (await* verified(tokenHex)) {
      case null { false };
      case (?p) { Admin.addAdmin(admin, p, Principal.fromText(whoText)) };
    };
  };

  public func removeAdmin(tokenHex : Text, whoText : Text) : async Bool {
    switch (await* verified(tokenHex)) {
      case null { false };
      case (?p) { Admin.removeAdmin(admin, p, Principal.fromText(whoText)) };
    };
  };

  public func transferOwner(tokenHex : Text, newOwnerText : Text) : async Bool {
    switch (await* verified(tokenHex)) {
      case null { false };
      case (?p) { Admin.transferOwner(admin, p, Principal.fromText(newOwnerText)) };
    };
  };

  public func setPaused(tokenHex : Text, v : Bool) : async Bool {
    switch (await* verified(tokenHex)) {
      case null { false };
      case (?p) { Admin.setPaused(admin, p, v) };
    };
  };
}
