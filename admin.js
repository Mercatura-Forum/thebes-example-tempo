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

  function afterCeremony(sessionPromise) {
    return sessionPromise.then(function (s) {
      return scoped(s);
    }).then(function (tok) {
      scopedTok = tok;
      return TempoAPI.checkAdmin(scopedTok);
    }).then(function (isAdmin) {
      if (isAdmin) return panel();
      return TempoAPI.hasOwner().then(function (owned) {
        if (!owned) return claimScreen();
        h('<aside class="adminp"><p>Signed in, but this passkey is not an admin.</p>' +
          '<p class="adminp__who">Fetching your principal…</p>' +
          '<p>An existing admin can add you with the principal above.</p>' +
          '<button class="adminp__x btn">Close</button></aside>');
        on('.adminp__x', 'click', close);
        TempoAPI.whoAmI(scopedTok).then(function (pr) {
          mount.querySelector('.adminp__who').textContent = 'Your principal: ' + (pr || '(could not verify)');
        }).catch(function () {
          mount.querySelector('.adminp__who').textContent = 'Your principal: (could not verify)';
        });
      });
    });
  }

  function open() {
    h('<aside class="adminp"><h3>TEMPO admin</h3><p>Sign in with your passkey. ' +
      'Works on the memphis origin only.</p>' +
      '<input class="adminp__name" placeholder="yourname.thebes" />' +
      '<div class="adminp__row"><button class="adminp__go btn btn--solid">Sign in</button>' +
      '<button class="adminp__x btn">Close</button></div>' +
      '<p class="adminp__note" hidden></p></aside>');
    on('.adminp__x', 'click', close);
    on('.adminp__go', 'click', function () {
      var name = mount.querySelector('.adminp__name').value.trim();
      // No awaits before the ceremony — it must run inside the user gesture.
      afterCeremony(MemphisPasskey.signInOrRegister(name)).catch(function (e) {
        if (e && e.code === 'NameNotRegistered') return offerCreate(e.nameRequested);
        toast('Sign-in failed: ' + (e && e.message));
      });
    });
  }

  function offerCreate(name) {
    var note = mount.querySelector('.adminp__note');
    note.hidden = false;
    note.textContent = 'No identity named ' + name + ' yet. Creating one runs THREE passkey ' +
      'confirmations in a row — Memphis signup requires three factors.';
    var go = mount.querySelector('.adminp__go');
    go.textContent = 'Create it';
    go.classList.add('adminp__create');
    var fresh = go.cloneNode(true); // drop the sign-in listener
    go.replaceWith(fresh);
    fresh.addEventListener('click', function () {
      // The granular signup ceremony: three device factors, then register.
      // The first WebAuthn create runs inside this click's gesture.
      var P = MemphisPasskey;
      afterCeremony(
        P.beginRegistrationChallenge().then(function (ch) {
          return P.buildDeviceFactor(ch, name).then(function (f1) {
            note.textContent = 'Factor 1 of 3 done — two more confirmations.';
            return P.buildDeviceFactor(ch, name).then(function (f2) {
              note.textContent = 'Factor 2 of 3 done — one more.';
              return P.buildDeviceFactor(ch, name).then(function (f3) {
                note.textContent = 'Registering with Memphis…';
                return P.registerWithFactors(name, [f1, f2, f3]);
              });
            });
          });
        })
      ).catch(function (e) { toast('Could not create it: ' + (e && e.message)); });
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
