/// Poll.mo — a recountable poll. One caller holds ONE standing vote; a revote
/// replaces it. The invariant sum(tallies) == distinct voters is RECOMPUTED
/// from the votes map on demand — there are no counters to drift.
import Map "mo:core/Map";
import Nat "mo:core/Nat";
import Principal "mo:core/Principal";

module {
  public type Candidate = { id : Nat; name : Text; blurb : Text };

  public type State = {
    var open : Bool;
    var nextId : Nat;
    candidates : Map.Map<Nat, Candidate>;
    votes : Map.Map<Principal, Nat>; // caller -> candidateId (latest wins)
  };

  public func new(seed : [(Text, Text)]) : State {
    let s : State = {
      var open = true;
      var nextId = 1;
      candidates = Map.empty<Nat, Candidate>();
      votes = Map.empty<Principal, Nat>();
    };
    for ((name, blurb) in seed.values()) { ignore addCandidate(s, name, blurb) };
    s;
  };

  public func addCandidate(s : State, name : Text, blurb : Text) : Nat {
    let id = s.nextId;
    s.nextId += 1;
    Map.add(s.candidates, Nat.compare, id, { id; name; blurb });
    id;
  };

  public func cast(s : State, caller : Principal, candidateId : Nat) : Bool {
    if (not s.open) return false;
    if (Map.get(s.candidates, Nat.compare, candidateId) == null) return false;
    Map.add(s.votes, Principal.compare, caller, candidateId);
    true;
  };

  public func myVote(s : State, caller : Principal) : ?Nat {
    Map.get(s.votes, Principal.compare, caller);
  };

  public func tally(s : State, candidateId : Nat) : Nat {
    var n = 0;
    for (v in Map.values(s.votes)) { if (v == candidateId) n += 1 };
    n;
  };

  public func totalVotes(s : State) : Nat { Map.size(s.votes) };

  public func sumTallies(s : State) : Nat {
    var n = 0;
    for (c in Map.values(s.candidates)) { n += tally(s, c.id) };
    n;
  };

  /// The property this example proves, recomputed fresh on every call.
  public func recountHolds(s : State) : Bool {
    sumTallies(s) == totalVotes(s);
  };
}
