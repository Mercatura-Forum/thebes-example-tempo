/*
 * admin.js — the passkey-gated admin drawer, shown only at #admin.
 * Sign-in is Memphis (passkey; works only on the memphis origin by RP_ID
 * design). Authority is checked ON-CHAIN: the contract verifies the scoped
 * session and keys admin rights to the derived per-app principal.
 */
(function () {
  'use strict';
  var mount = document.getElementById('adminMount');
  var scopedTok = null;

  function h(html) { mount.innerHTML = html; }
  function on(sel, ev, fn) { mount.querySelector(sel).addEventListener(ev, fn); }
  function toast(m) { (window.TEMPO && TEMPO.toast) ? TEMPO.toast(m) : alert(m); }

  async function scoped(session) {
    var r = await MemphisPasskey.issueScopedSession(session.session_token_hex, TempoAPI.AUDIENCE);
    return r.scoped_token_hex;
  }

  function open() {
    h('<aside class="adminp"><h3>TEMPO admin</h3><p>Sign in with your passkey. ' +
      'Works on the memphis origin only.</p>' +
      '<input class="adminp__name" placeholder="account name" />' +
      '<div class="adminp__row"><button class="adminp__go btn btn--solid">Sign in</button>' +
      '<button class="adminp__x btn">Close</button></div></aside>');
    on('.adminp__x', 'click', close);
    on('.adminp__go', 'click', function () {
      var name = mount.querySelector('.adminp__name').value.trim();
      // No awaits before the ceremony — it must run inside the user gesture.
      MemphisPasskey.signInOrRegister(name).then(function (s) {
        return scoped(s);
      }).then(function (tok) {
        scopedTok = tok;
        return TempoAPI.checkAdmin(scopedTok);
      }).then(function (isAdmin) {
        if (isAdmin) return panel();
        return TempoAPI.hasOwner().then(function (owned) {
          if (!owned) return claimScreen();
          h('<aside class="adminp"><p>Signed in, but this passkey is not an admin.</p>' +
            '<button class="adminp__x btn">Close</button></aside>');
          on('.adminp__x', 'click', close);
        });
      }).catch(function (e) { toast('Sign-in failed: ' + (e && e.message)); });
    });
  }

  function claimScreen() {
    h('<aside class="adminp"><h3>TEMPO admin</h3><p>No owner yet. Claim it?</p>' +
      '<div class="adminp__row"><button class="adminp__go btn btn--solid">Claim ownership</button>' +
      '<button class="adminp__x btn">Close</button></div></aside>');
    on('.adminp__x', 'click', close);
    on('.adminp__go', 'click', async function () {
      try { if (await TempoAPI.claimOwner(scopedTok)) panel(); else toast('Claim refused'); }
      catch (e) { toast('Claim failed: ' + (e && e.message)); }
    });
  }

  async function panel() {
    var skus = await TempoAPI.fetchSkus();
    var poll = await TempoAPI.fetchPoll();
    h('<aside class="adminp"><h3>TEMPO admin</h3>' +
      '<section>' + skus.map(function (s) {
        return '<div class="adminp__row" data-id="' + s.id + '"><b>' + s.name + '</b>' +
          '<input class="adminp__price" value="' + Math.round(s.pricePiastres / 100) + '" size="4" inputmode="numeric" /> EGP ' +
          '<select class="adminp__stock">' + ['in', 'low', 'out'].map(function (o) {
            return '<option' + (o === s.stock ? ' selected' : '') + '>' + o + '</option>';
          }).join('') + '</select>' +
          '<button class="adminp__save btn">Save</button></div>';
      }).join('') + '</section>' +
      '<section class="adminp__row"><label>Poll open <input type="checkbox" class="adminp__pollopen"' +
        (poll.length && poll[0].open ? ' checked' : '') + ' /></label></section>' +
      '<p class="adminp__who"></p>' +
      '<section class="adminp__row"><input class="adminp__newadmin" placeholder="principal to add as admin" />' +
      '<button class="adminp__addadmin btn">Add admin</button></section>' +
      '<button class="adminp__x btn">Close</button></aside>');
    on('.adminp__x', 'click', close);
    TempoAPI.whoAmI(scopedTok).then(function (p) {
      mount.querySelector('.adminp__who').textContent = 'Your admin principal: ' + p;
    }).catch(function () {});
    on('.adminp__addadmin', 'click', async function () {
      try {
        var who = mount.querySelector('.adminp__newadmin').value.trim();
        if (await TempoAPI.addAdmin(scopedTok, who)) toast('Admin added'); else toast('Refused (owner only)');
      } catch (e) { toast('Failed: ' + (e && e.message)); }
    });
    mount.querySelectorAll('.adminp__row[data-id]').forEach(function (row) {
      row.querySelector('.adminp__save').addEventListener('click', async function () {
        var id = Number(row.dataset.id);
        try {
          await TempoAPI.setSkuPrice(scopedTok, id, Number(row.querySelector('.adminp__price').value) * 100);
          await TempoAPI.setSkuStock(scopedTok, id, row.querySelector('.adminp__stock').value);
          toast('Saved');
          window.location.reload();
        } catch (e) { toast('Save failed: ' + (e && e.message)); }
      });
    });
    on('.adminp__pollopen', 'change', async function (ev) {
      try { await TempoAPI.setPollOpen(scopedTok, ev.target.checked); toast('Poll updated'); }
      catch (e) { toast('Failed: ' + (e && e.message)); }
    });
  }

  function close() {
    mount.innerHTML = '';
    if (location.hash === '#admin') history.replaceState(null, '', location.pathname);
  }
  function maybe() { if (location.hash === '#admin') open(); }
  window.addEventListener('hashchange', maybe);
  maybe();
})();
