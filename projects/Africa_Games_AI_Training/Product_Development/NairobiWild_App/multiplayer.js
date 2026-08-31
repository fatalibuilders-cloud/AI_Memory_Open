/*
 * Nairobi Wild — multiplayer
 *
 * Three ways to play against another person, behind one interface so the
 * game screen never knows which is in use:
 *
 *   LOCAL  — pass and play on one phone. Fully offline.
 *   LINK   — asynchronous challenge. You play a board, then share a link
 *            (WhatsApp, SMS) carrying the seed and your score; your friend
 *            plays THE SAME board and the app compares. No server, works
 *            offline, and the share is the growth loop.
 *   ONLINE — live head-to-head. Both players get the same board from a
 *            shared seed and see each other's score update as they play.
 *
 * How ONLINE works without us running a server: the published page is
 * granted the `room` capability, which gives every open copy of the page a
 * shared presence channel. Each player publishes their own state — nickname,
 * seed, score, moves left, finished — and reads everyone else's. Presence is
 * settable by any viewer (unlike events, which are admin-only by default),
 * so the entire lobby-and-duel handshake is built on presence alone.
 *
 * FAIRNESS NOTE: scores here are client-reported, which is fine for playing
 * with friends but is NOT cheat-proof. A ranked/leaderboard mode needs the
 * authoritative server described in the architecture doc — the engine is
 * deterministic, so a server can replay a move list and verify the score.
 *
 * For the production Android build, `RealtimeAdapter` is the seam to
 * implement against a WebSocket service; nothing else in the game changes.
 */
(function (global) {
  'use strict';

  const PRESENCE_MS = 250;      // how often we push our own state at most
  const STALE_MS = 45000;       // peers quiet longer than this are ignored

  /* ---------- shared helpers ---------- */

  function randomSeed() {
    return Math.floor(Math.random() * 1e9);
  }

  /* Challenge links: #d=<seed>.<score>.<base64 nickname> */
  function encodeChallenge(seed, score, nick) {
    const safe = String(nick || 'A friend').slice(0, 16);
    let b64;
    try {
      b64 = btoa(unescape(encodeURIComponent(safe))).replace(/=+$/, '');
    } catch (e) {
      b64 = '';
    }
    return 'd=' + [seed, Math.max(0, Math.round(score)), b64].join('.');
  }

  function decodeChallenge(hash) {
    if (!hash) return null;
    const m = String(hash).replace(/^#/, '').match(/(?:^|&)d=([^&]+)/);
    if (!m) return null;
    const parts = m[1].split('.');
    if (parts.length < 2) return null;
    const seed = Number(parts[0]);
    const score = Number(parts[1]);
    if (!Number.isFinite(seed) || !Number.isFinite(score)) return null;
    let nick = 'A friend';
    if (parts[2]) {
      try {
        nick = decodeURIComponent(escape(atob(parts[2] + '==='.slice((parts[2].length + 3) % 4))));
      } catch (e) { /* keep the default */ }
    }
    return { seed, score, nick: nick.slice(0, 16) };
  }

  function challengeUrl(base, seed, score, nick) {
    const clean = String(base).split('#')[0];
    return clean + '#' + encodeChallenge(seed, score, nick);
  }

  /* ---------- ONLINE: the room-backed adapter ---------- */

  /*
   * Duel handshake, entirely in presence:
   *   1. Host sets   { st:'host',  seed }
   *   2. Guest sees the host, sets { st:'join', seed:<host seed>, vs:<host peer> }
   *   3. Host sees a guest pointing at it, locks on to the FIRST one and
   *      sets { st:'duel', vs:<guest peer> }
   *   4. Guest sees the host point back → both start on the same seed.
   * Anyone not chosen falls back to the lobby.
   */
  function RoomAdapter(room) {
    this.room = room;
    this.me = null;              // my peer label, learned from peers()
    this.nick = 'Mwindaji';
    this.state = { st: 'lobby' };
    this._lastPush = 0;
    this._pending = null;
    this._subs = [];
    this.onChange = null;

    const push = () => {
      this._lastPush = Date.now();
      this._pending = null;
      this.room.presence({ ...this.state, nick: this.nick, ts: Date.now() })
        .catch(() => { /* presence is best-effort; the game plays on */ });
    };
    this._push = () => {
      const since = Date.now() - this._lastPush;
      if (since >= PRESENCE_MS) { push(); return; }
      if (this._pending) return;
      this._pending = setTimeout(push, PRESENCE_MS - since);
    };

    // A player who is thinking sends nothing, and would look stale — and
    // then be treated as having quit. A slow heartbeat keeps them present.
    this._beat = setInterval(() => this._push(), Math.floor(STALE_MS / 3));
    // Under Node (the test suite) a bare interval would keep the process
    // alive forever; in a browser setInterval returns a number and this
    // is simply skipped.
    if (this._beat && typeof this._beat.unref === 'function') this._beat.unref();

    this._subs.push(this.room.onPeers((change) => {
      const mine = change.peers.find((p) => p.isMe && p.sameTab);
      if (mine) this.me = mine.peer;
      if (this.onChange) this.onChange(this.peers(), change);
    }, () => { if (this.onChange) this.onChange([], null); }));
  }

  RoomAdapter.prototype.setNick = function (nick) {
    this.nick = String(nick || 'Mwindaji').slice(0, 16);
    this._push();
  };

  RoomAdapter.prototype.set = function (patch) {
    this.state = { ...this.state, ...patch };
    this._push();
  };

  /* Everyone here but me, recent enough to be real. */
  RoomAdapter.prototype.peers = function () {
    const now = Date.now();
    return this.room.peers()
      .filter((p) => !p.isMe && p.kind === 'viewer')
      .filter((p) => p.presence && typeof p.presence === 'object')
      .filter((p) => !p.presence.ts || now - p.presence.ts < STALE_MS)
      .map((p) => ({
        peer: p.peer,
        nick: typeof p.presence.nick === 'string' ? p.presence.nick.slice(0, 16) : 'Mwindaji',
        st: p.presence.st,
        seed: Number(p.presence.seed) || 0,
        vs: typeof p.presence.vs === 'string' ? p.presence.vs : null,
        score: Number(p.presence.score) || 0,
        moves: Number(p.presence.moves) || 0,
        done: !!p.presence.done,
      }));
  };

  RoomAdapter.prototype.openHosts = function () {
    return this.peers().filter((p) => p.st === 'host');
  };

  /* The peer I am duelling, if we have both pointed at each other. */
  RoomAdapter.prototype.opponent = function () {
    if (!this.state.vs) return null;
    return this.peers().find((p) => p.peer === this.state.vs) || null;
  };

  RoomAdapter.prototype.dispose = function () {
    this._subs.forEach((u) => { try { u(); } catch (e) {} });
    this._subs = [];
    clearInterval(this._beat);
    clearTimeout(this._pending);
    try { this.room.presence({ st: null, seed: null, vs: null, score: null, moves: null, done: null }); } catch (e) {}
  };

  /*
   * Production seam: implement this against a WebSocket service to get the
   * same duel in the standalone Android build (where `room` does not exist).
   * Same method surface as RoomAdapter, so the UI is unchanged.
   */
  function RealtimeAdapter() {
    throw new Error('RealtimeAdapter: not implemented — see NairobiWild_architecture.md');
  }

  const Multiplayer = {
    PRESENCE_MS, STALE_MS,
    randomSeed, encodeChallenge, decodeChallenge, challengeUrl,
    RoomAdapter, RealtimeAdapter,
  };

  if (typeof module !== 'undefined' && module.exports) module.exports = Multiplayer;
  else global.NairobiMP = Multiplayer;
})(typeof window !== 'undefined' ? window : globalThis);
