// Interpreter-run unit checks for the pure modules. Run:
//   moc -r $(mops sources) test/units.test.mo
// Any failed check traps, which exits nonzero.
import Principal "mo:core/Principal";
import Runtime "mo:core/Runtime";
import Hex "../Hex";
import Poll "../Poll";

func check(ok : Bool, name : Text) {
  if (not ok) Runtime.trap("FAIL: " # name);
};

// ── Hex ──
check(Hex.toBlob("00ff10") == ?("\00\ff\10" : Blob), "hex decodes bytes");
check(Hex.toBlob("") == ?("" : Blob), "empty hex is the empty blob");
check(Hex.toBlob("abc") == null, "odd length is refused");
check(Hex.toBlob("zz") == null, "non-hex is refused");
check(Hex.toBlob("DEadBEef") == ?("\de\ad\be\ef" : Blob), "mixed case decodes");

// ── Poll ──
let p = Poll.new([("Mango Surge", "b1"), ("Tamarind Volt", "b2")]);
let alice = Principal.fromBlob("\04\01");
let bob = Principal.fromBlob("\04\02");
check(Poll.tally(p, 1) == 0, "fresh poll has zero tally");
check(Poll.cast(p, alice, 1), "vote lands");
check(Poll.tally(p, 1) == 1, "tally counts the vote");
check(Poll.cast(p, alice, 2), "revote lands");
check(Poll.tally(p, 1) == 0 and Poll.tally(p, 2) == 1, "revote REPLACES, never adds");
check(Poll.totalVotes(p) == 1, "one distinct voter");
check(Poll.cast(p, bob, 1), "second voter lands");
check(Poll.sumTallies(p) == 2 and Poll.totalVotes(p) == 2, "sum == distinct");
check(Poll.recountHolds(p), "the recount invariant holds");
check(not Poll.cast(p, alice, 99), "unknown candidate refused");
check(Poll.myVote(p, alice) == ?2, "standing vote readable");
check(Poll.myVote(p, Principal.fromBlob("\04\09")) == null, "no vote is null");
p.open := false;
check(not Poll.cast(p, bob, 2), "closed poll refuses");
check(Poll.recountHolds(p), "invariant survives the refusals");
let id3 = Poll.addCandidate(p, "Mint Lime", "b3");
check(id3 == 3, "candidate ids increment");
