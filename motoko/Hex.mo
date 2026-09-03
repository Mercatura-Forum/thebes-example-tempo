/// Hex.mo — decode a hex string to a Blob. Pure and total: bad input yields
/// null, never a trap.
import Char "mo:core/Char";
import Nat8 "mo:core/Nat8";
import Nat32 "mo:core/Nat32";
import List "mo:core/List";
import Blob "mo:core/Blob";

module {
  func nibble(c : Char) : ?Nat8 {
    let n = Char.toNat32(c);
    if (n >= 48 and n <= 57) return ?Nat8.fromNat(Nat32.toNat(n - 48)); // 0-9
    if (n >= 97 and n <= 102) return ?Nat8.fromNat(Nat32.toNat(n - 87)); // a-f
    if (n >= 65 and n <= 70) return ?Nat8.fromNat(Nat32.toNat(n - 55)); // A-F
    null;
  };

  /// "00ff10" -> ?Blob. Odd length or a non-hex character yields null.
  public func toBlob(t : Text) : ?Blob {
    let out = List.empty<Nat8>();
    var hi : ?Nat8 = null;
    for (c in t.chars()) {
      switch (nibble(c)) {
        case null { return null };
        case (?n) {
          switch (hi) {
            case null { hi := ?n };
            case (?h) { List.add(out, h * 16 + n); hi := null };
          };
        };
      };
    };
    if (hi != null) return null; // odd length
    ?Blob.fromArray(List.toArray(out));
  };
}
