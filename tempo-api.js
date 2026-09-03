/*
 * tempo-api.js — the site's typed verbs over the SDK runtime (window.EgyptBoundary).
 * Plain script, no build step: this is the whole SDK integration.
 * Reads are flat *View queries; writes go through the boundary's receipt flow.
 * Safety split (the SDK's own semantics): a call with NO message_hash was never
 * accepted — resubmit-safe; a receipt TIMEOUT may have landed — never auto-resubmit.
 */
(function () {
  'use strict';
  var CID = 148286166025860; // pinned to the minted contract id at deploy time
  var AUDIENCE = 'https://memphis.mercaturaforum.com';

  function B() {
    if (!window.EgyptBoundary) throw new Error('boundary.js not loaded');
    return window.EgyptBoundary;
  }
  function replyOf(r) { return (r && (r.reply_hex || r.reply)) || ''; }
  function num(v) { return typeof v === 'bigint' ? Number(v) : v; }

  async function rows(method, fields) {
    var r = await B().callQuery(CID, method, null);
    var hex = replyOf(r);
    if (!hex) throw new Error(method + ': no reply');
    return B().decodeVecRecord(hex, fields).map(function (row) {
      var out = {};
      for (var k in row) out[k] = num(row[k]);
      return out;
    });
  }

  async function call(method, argHex, opts) {
    var r;
    try {
      r = await B().callUpdate(CID, method, argHex, opts || {});
    } catch (e) {
      if (String(e && e.message).indexOf('timed out') >= 0) e.mayHaveLanded = true;
      else e.safeToRetry = true; // rejected before acceptance: no message_hash
      throw e;
    }
    if (r.status === 'error') throw new Error(method + ': ' + (r.error || 'error'));
    var hex = replyOf(r);
    return hex ? B().decodeBoolReply(hex) : true;
  }

  var t = function (v) { return { type: 'text', value: v }; };
  var n = function (v) { return { type: 'nat', value: BigInt(v) }; };
  var b = function (v) { return { type: 'bool', value: !!v }; };
  var hexArgs = function (list) { return B().bytesToHex(B().encodeArgs(list)); };
  var hexArg = function (one) { return B().bytesToHex(B().encodeArg(one)); };

  var SKU_FIELDS = [
    { name: 'id', type: 'nat' }, { name: 'name', type: 'text' }, { name: 'desc', type: 'text' },
    { name: 'pricePiastres', type: 'nat' }, { name: 'unit', type: 'text' }, { name: 'tag', type: 'text' },
    { name: 'featured', type: 'bool' }, { name: 'stock', type: 'text' }, { name: 'sortOrder', type: 'nat' },
  ];
  var STOCKIST_FIELDS = [
    { name: 'id', type: 'nat' }, { name: 'city', type: 'text' }, { name: 'meta', type: 'text' },
    { name: 'spots', type: 'nat' }, { name: 'lonMilli', type: 'nat' }, { name: 'latMilli', type: 'nat' },
  ];
  var POLL_FIELDS = [
    { name: 'id', type: 'nat' }, { name: 'name', type: 'text' }, { name: 'blurb', type: 'text' },
    { name: 'tally', type: 'nat' }, { name: 'open', type: 'bool' }, { name: 'totalVotes', type: 'nat' },
  ];
  var RECOUNT_FIELDS = [
    { name: 'candidateId', type: 'nat' }, { name: 'tally', type: 'nat' },
    { name: 'distinctVoters', type: 'nat' }, { name: 'sumTallies', type: 'nat' }, { name: 'holds', type: 'bool' },
  ];
  var MYVOTE_FIELDS = [{ name: 'candidateId', type: 'nat' }];

  window.TempoAPI = {
    AUDIENCE: AUDIENCE,
    cid: function () { return CID; },
    _setCid: function (v) { CID = v; },

    fetchSkus: function () { return rows('skusView', SKU_FIELDS); },
    fetchStockists: function () { return rows('stockistsView', STOCKIST_FIELDS); },
    fetchPoll: function () { return rows('pollView', POLL_FIELDS); },
    fetchRecount: function () { return rows('recountView', RECOUNT_FIELDS); },
    fetchMyVote: function () {
      return rows('myVoteView', MYVOTE_FIELDS).then(function (r) { return r.length ? r[0].candidateId : null; });
    },

    castVote: function (id, opts) { return call('castVote', hexArg(n(id)), opts); },

    hasOwner: async function () {
      var r = await B().callQuery(CID, 'hasOwner', null);
      var hex = replyOf(r);
      if (!hex) throw new Error('hasOwner: no reply');
      return B().decodeBoolReply(hex);
    },
    checkAdmin: function (tok) { return call('checkAdmin', hexArg(t(tok))); },
    claimOwner: function (tok) { return call('claimOwner', hexArg(t(tok))); },
    setSkuPrice: function (tok, id, p) { return call('setSkuPrice', hexArgs([t(tok), n(id), n(p)])); },
    setSkuStock: function (tok, id, s) { return call('setSkuStock', hexArgs([t(tok), n(id), t(s)])); },
    upsertStockist: function (tok, s) {
      return call('upsertStockist', hexArgs([t(tok), n(s.id || 0), t(s.city), t(s.meta), n(s.spots), n(s.lonMilli), n(s.latMilli)]));
    },
    setPollOpen: function (tok, open) { return call('setPollOpen', hexArgs([t(tok), b(open)])); },
    addCandidate: function (tok, name, blurb) { return call('addCandidate', hexArgs([t(tok), t(name), t(blurb)])); },
    whoAmI: async function (tok) {
      // Text reply in a fixed shape: DIDL, empty table (00), one arg (01),
      // type text (0x71), then uleb length + utf8 bytes.
      var r = await B().callUpdate(CID, 'whoAmI', hexArg(t(tok)), {});
      var hex = replyOf(r); if (!hex) return '';
      var bytes = B().hexToBytes(hex);
      var at = 4 + 1 + 1 + 1;
      var len = B().readUleb(bytes, at); // [value, nextIndex]
      return new TextDecoder().decode(bytes.subarray(Number(len[1]), Number(len[1]) + Number(len[0])));
    },
    addAdmin: function (tok, whoText) { return call('addAdmin', hexArgs([t(tok), t(whoText)])); },
    removeAdmin: function (tok, whoText) { return call('removeAdmin', hexArgs([t(tok), t(whoText)])); },
    transferOwner: function (tok, whoText) { return call('transferOwner', hexArgs([t(tok), t(whoText)])); },
  };
})();
