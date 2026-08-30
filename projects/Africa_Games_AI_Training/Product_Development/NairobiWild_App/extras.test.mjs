/*
 * Nairobi Wild — music + multiplayer tests.  Run with: node extras.test.mjs
 * (Engine rules live in match3.test.mjs.)
 */
import { createRequire } from 'node:module';
import assert from 'node:assert/strict';

const require = createRequire(import.meta.url);
// Both modules attach to globalThis when there is no `window`.
const Music = require('./music.js');
const MP = require('./multiplayer.js');
const M = require('./match3.js');

let passed = 0;
function test(name, fn) {
  try { fn(); passed += 1; console.log('  ✓ ' + name); }
  catch (err) { console.error('  ✗ ' + name); console.error(err); process.exitCode = 1; }
}

/* ---------------- music ---------------- */

test('every drum pattern stays inside the bar', () => {
  for (let bar = 0; bar < Music.BARS; bar += 1) {
    [Music.kickPattern(bar), Music.shakerPattern(), Music.clapPattern()].forEach((pat) => {
      pat.forEach((s) => {
        assert.ok(Number.isInteger(s), 'step is an integer');
        assert.ok(s >= 0 && s < Music.STEPS, 'step ' + s + ' inside the bar');
      });
    });
  }
});

test('the kick lands four-on-the-floor in every bar', () => {
  for (let bar = 0; bar < Music.BARS; bar += 1) {
    const k = Music.kickPattern(bar);
    [0, 4, 8, 12].forEach((beat) => assert.ok(k.includes(beat), 'bar ' + bar + ' beat ' + beat));
  }
});

test('the clap answers on the backbeat, not the downbeat', () => {
  const c = Music.clapPattern();
  assert.deepEqual(c, [4, 12]);
  assert.ok(!c.includes(0), 'never on the one');
});

test('the shaker runs continuous 16ths (the kayamba pulse)', () => {
  assert.equal(Music.shakerPattern().length, Music.STEPS);
});

test('bass and riff notes are audible, in-tune frequencies', () => {
  for (let bar = 0; bar < Music.BARS; bar += 1) {
    [...Music.bassPattern(bar), ...Music.riffPattern(bar), ...Music.marimbaPattern(bar)].forEach((n) => {
      assert.ok(n.step >= 0 && n.step < Music.STEPS, 'step in bar');
      assert.ok(n.freq > 20 && n.freq < 20000, 'frequency ' + n.freq + ' is audible');
    });
  }
});

test('the riff is a cycling 8th-note figure that moves each bar', () => {
  const a = Music.riffPattern(0).map((n) => Math.round(n.freq));
  const b = Music.riffPattern(1).map((n) => Math.round(n.freq));
  assert.equal(a.length, 8, 'eight plucks to the bar');
  assert.notDeepEqual(a, b, 'the phrase shifts rather than looping flat');
  Music.riffPattern(0).forEach((n) => assert.equal(n.step % 2, 0, 'straight 8ths'));
});

test('riff and bass stay in the pentatonic scale', () => {
  const inScale = (f) => Music.SCALE.some((s) => {
    for (let oct = 0.25; oct <= 8; oct *= 2) if (Math.abs(s * oct - f) < 0.5) return true;
    return false;
  });
  for (let bar = 0; bar < Music.BARS; bar += 1) {
    Music.riffPattern(bar).forEach((n) => assert.ok(inScale(n.freq), 'riff note ' + n.freq + ' in scale'));
    Music.marimbaPattern(bar).forEach((n) => assert.ok(inScale(n.freq), 'marimba note in scale'));
  }
});

test('the marimba layer is sparse — it answers, it does not chatter', () => {
  let total = 0;
  for (let bar = 0; bar < Music.BARS; bar += 1) total += Music.marimbaPattern(bar).length;
  assert.ok(total > 0, 'it does play');
  assert.ok(total < Music.BARS * 4, 'but stays out of the way');
});

test('the engine constructs and degrades quietly with no WebAudio', () => {
  const e = new Music.Engine();
  assert.equal(e.playing, false);
  e.start();                       // no AudioContext under Node
  assert.equal(e.playing, false, 'start() must not throw or fake playback');
  e.setEnergy(2); e.setVolume(0.3); e.flourish(); e.stop();
});

/* ---------------- multiplayer ---------------- */

test('a challenge round-trips through a link', () => {
  const link = MP.encodeChallenge(123456, 8400, 'Wanjiru');
  const back = MP.decodeChallenge('#' + link);
  assert.equal(back.seed, 123456);
  assert.equal(back.score, 8400);
  assert.equal(back.nick, 'Wanjiru');
});

test('challenge links survive accents and emoji in a nickname', () => {
  const back = MP.decodeChallenge('#' + MP.encodeChallenge(7, 10, 'Zawadi 🦁'));
  assert.equal(back.nick, 'Zawadi 🦁');
});

test('a challenge link builds a full shareable URL', () => {
  const url = MP.challengeUrl('https://example.com/game#old', 42, 900, 'Otieno');
  assert.ok(url.startsWith('https://example.com/game#d=42.900.'), url);
  assert.equal(url.split('#').length, 2, 'exactly one hash');
  assert.equal(MP.decodeChallenge(url.split('#')[1]).seed, 42);
});

test('rubbish links decode to null instead of starting a broken duel', () => {
  ['', '#', '#nonsense', '#d=', '#d=abc.def', null, undefined].forEach((bad) => {
    assert.equal(MP.decodeChallenge(bad), null, JSON.stringify(bad));
  });
});

test('a shared seed produces an identical board for both players', () => {
  const seed = MP.randomSeed();
  const a = M.newGame(M.DUEL_LEVEL, seed);
  const b = M.newGame(M.DUEL_LEVEL, seed);
  assert.deepEqual(
    a.board.map((t) => t.c + ':' + t.s),
    b.board.map((t) => t.c + ':' + t.s),
    'duel boards must match exactly'
  );
  assert.equal(a.movesLeft, M.DUEL_MOVES);
});

test('different seeds produce different boards', () => {
  const a = M.newGame(M.DUEL_LEVEL, 1).board.map((t) => t.c).join('');
  const b = M.newGame(M.DUEL_LEVEL, 2).board.map((t) => t.c).join('');
  assert.notEqual(a, b);
});

test('a duel is decided on score alone, with no collect goals', () => {
  assert.deepEqual(M.DUEL_LEVEL.collect, []);
  const s = M.newGame(M.DUEL_LEVEL, 5);
  s.score = 50000;
  assert.equal(M.goalsMet(s), false, 'no early win — a duel always runs its full moves');
});

/* A tiny fake of the room capability, to prove the handshake. */
function fakeRoom() {
  const peers = [];
  const listeners = [];
  return {
    _peers: peers,
    _fire() { const c = { peers, joined: [], left: [], updated: [] }; listeners.forEach((f) => f(c)); },
    _add(p) { peers.push(p); this._fire(); },
    peers: () => peers,
    onPeers(fn) { listeners.push(fn); return () => {}; },
    presence(patch) {
      const mine = peers.find((p) => p.isMe && p.sameTab);
      if (mine) Object.keys(patch).forEach((k) => {
        if (patch[k] === null) delete mine.presence[k]; else mine.presence[k] = patch[k];
      });
      return Promise.resolve();
    },
  };
}

test('the room adapter learns my own peer label and ignores me in the lobby', () => {
  const room = fakeRoom();
  const a = new MP.RoomAdapter(room);
  room._add({ peer: 'me1', isMe: true, sameTab: true, kind: 'viewer', presence: {} });
  assert.equal(a.me, 'me1');
  assert.equal(a.peers().length, 0, 'I am never my own opponent');
});

test('the room adapter lists open hosts and finds the locked-on opponent', () => {
  const room = fakeRoom();
  const a = new MP.RoomAdapter(room);
  room._add({ peer: 'me1', isMe: true, sameTab: true, kind: 'viewer', presence: {} });
  room._add({ peer: 'h1', isMe: false, sameTab: false, kind: 'viewer',
    presence: { st: 'host', seed: 99, nick: 'Kamau', ts: Date.now() } });
  room._add({ peer: 'x1', isMe: false, sameTab: false, kind: 'viewer',
    presence: { st: 'lobby', nick: 'Idle', ts: Date.now() } });

  const hosts = a.openHosts();
  assert.equal(hosts.length, 1);
  assert.equal(hosts[0].nick, 'Kamau');
  assert.equal(hosts[0].seed, 99);

  assert.equal(a.opponent(), null, 'nobody locked on yet');
  a.set({ st: 'duel', seed: 99, vs: 'h1' });
  assert.equal(a.opponent().peer, 'h1');
});

test('stale and non-viewer peers are filtered out of the lobby', () => {
  const room = fakeRoom();
  const a = new MP.RoomAdapter(room);
  room._add({ peer: 'me1', isMe: true, sameTab: true, kind: 'viewer', presence: {} });
  room._add({ peer: 'ghost', isMe: false, sameTab: false, kind: 'viewer',
    presence: { st: 'host', seed: 1, ts: Date.now() - (MP.STALE_MS + 5000) } });
  room._add({ peer: 'bot', isMe: false, sameTab: false, kind: 'agent',
    presence: { st: 'host', seed: 2, ts: Date.now() } });
  assert.equal(a.openHosts().length, 0, 'no ghosts, no agents');
});

test('opponent state is read defensively — a hostile peer cannot break us', () => {
  const room = fakeRoom();
  const a = new MP.RoomAdapter(room);
  room._add({ peer: 'me1', isMe: true, sameTab: true, kind: 'viewer', presence: {} });
  room._add({ peer: 'bad', isMe: false, sameTab: false, kind: 'viewer',
    presence: { st: 'host', seed: 'not-a-number', nick: { evil: true }, score: 'NaN', ts: Date.now() } });
  const p = a.peers()[0];
  assert.equal(p.seed, 0);
  assert.equal(p.score, 0);
  assert.equal(typeof p.nick, 'string', 'a non-string nickname never reaches the DOM');
});

test('a long nickname is clipped before it is published', () => {
  const room = fakeRoom();
  const a = new MP.RoomAdapter(room);
  room._add({ peer: 'me1', isMe: true, sameTab: true, kind: 'viewer', presence: {} });
  a.setNick('X'.repeat(120));
  assert.ok(a.nick.length <= 16);
});

console.log('\n' + passed + ' tests passed' + (process.exitCode ? ' (with failures)' : ''));
