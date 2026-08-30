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
const SND = require('./sounds.js');
const MON = require('./monetization.js');

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

/* ---------------- animal voices ---------------- */

test('every animal has its own voice', () => {
  assert.equal(SND.SPECS.length, M.COLORS, 'one call per animal');
  const names = SND.SPECS.map((s) => s.name);
  assert.deepEqual(names, ['Simba', 'Tembo', 'Punda Milia', 'Twiga', 'Kifaru', 'Chui']);
  assert.equal(new Set(names).size, names.length);
});

test('voice specs are physically sane — audible, short, not deafening', () => {
  SND.SPECS.forEach((s) => {
    [s.f0, s.f1, s.noiseFreq, s.filterFrom, s.filterTo].forEach((f) => {
      assert.ok(f > 20 && f < 20000, s.name + ' frequency ' + f + ' is audible');
    });
    assert.ok(s.gain > 0 && s.gain <= 0.6, s.name + ' gain is polite');
    assert.ok(s.noise >= 0 && s.noise <= 1, s.name + ' noise in range');
    assert.ok(s.pulses >= 1 && s.pulses <= 8, s.name + ' pulse count');
    assert.ok(s.attack > 0 && s.attack < s.pulseDur, s.name + ' attack fits the pulse');
    // These fire on every match — anything long becomes torture.
    assert.ok(SND.totalDuration(s) <= 1.0, s.name + ' call is ' + SND.totalDuration(s) + 's');
  });
});

test('each call has a distinct character, not six versions of one beep', () => {
  const fingerprints = SND.SPECS.map((s) => [s.type, s.pulses, Math.round(s.f0), Math.round(s.noise * 10)].join('/'));
  assert.equal(new Set(fingerprints).size, fingerprints.length, 'all six differ');
});

test('the lion roars low, the zebra barks high', () => {
  const lion = SND.voiceSpec(0);
  const zebra = SND.voiceSpec(2);
  assert.ok(lion.f0 < zebra.f0, 'a roar sits below a bark');
  assert.ok(lion.f1 < lion.f0, 'a roar falls in pitch');
  assert.ok(lion.tremoloDepth > 0, 'a roar rumbles');
  assert.ok(SND.totalDuration(lion) > SND.totalDuration(zebra), 'a roar outlasts a bark');
});

test('the elephant trumpet rises; the giraffe hums near 92 Hz', () => {
  const tembo = SND.voiceSpec(1);
  assert.ok(tembo.f1 > tembo.f0, 'a trumpet climbs');
  const twiga = SND.voiceSpec(3);
  assert.ok(Math.abs(twiga.f0 - 92) < 6, 'giraffes hum at about 92 Hz');
});

test("the leopard's sawing call repeats; most others are single", () => {
  assert.ok(SND.voiceSpec(5).pulses >= 4, 'a rasp is many strokes');
  assert.equal(SND.voiceSpec(0).pulses, 1);
  assert.equal(SND.pulseTimes(SND.voiceSpec(5)).length, SND.voiceSpec(5).pulses);
});

test('pulse timings run forward and never overlap', () => {
  SND.SPECS.forEach((s) => {
    const t = SND.pulseTimes(s);
    for (let i = 1; i < t.length; i += 1) {
      assert.ok(t[i] >= t[i - 1] + s.pulseDur, s.name + ' pulses do not overlap');
    }
  });
});

test('voiceSpec is total — any colour index resolves to a real voice', () => {
  [0, 5, 6, 12, -1, -7].forEach((i) => {
    assert.ok(SND.voiceSpec(i) && SND.voiceSpec(i).name, 'index ' + i);
  });
});

test('voices degrade quietly with no WebAudio', () => {
  const v = new SND.AnimalVoices();
  v.attach(null);
  v.play(0, { combo: 3 });   // must not throw
  v.setVolume(0.5);
});

/* ---------------- monetization ---------------- */

test('the shop catalogue is complete and priced', () => {
  assert.ok(MON.PRODUCTS.length >= 5);
  MON.PRODUCTS.forEach((p) => {
    assert.ok(p.id && p.label && p.note, 'product ' + p.id + ' is described');
    assert.ok(p.usd > 0 && p.usd < 100, p.id + ' has a sane price');
    assert.ok(p.coins || p.lives, p.id + ' actually gives something');
  });
  assert.equal(new Set(MON.PRODUCTS.map((p) => p.id)).size, MON.PRODUCTS.length, 'ids unique');
});

test('nothing sold confers a gameplay advantage that cannot be earned free', () => {
  const kinds = new Set(MON.PRODUCTS.map((p) => p.kind));
  ['coins', 'bundle', 'lives', 'support'].forEach((k) => assert.ok(kinds.has(k), k));
  // No product may skip levels or buy difficulty.
  MON.PRODUCTS.forEach((p) => {
    assert.ok(!/skip|unlock_level|win/i.test(p.id), p.id + ' must not sell progress');
  });
});

test('prices are shown in local currency when one is configured', () => {
  const p = MON.productById('coins_500');
  const kes = MON.priceLabel(p, { web: { currency: 'KES', usdToLocal: 129 } });
  assert.ok(kes.startsWith('KES '), kes);
  const usd = MON.priceLabel(p, { web: { currency: 'USD', usdToLocal: 1 } });
  assert.equal(usd, '$0.99');
});

test('the provider is chosen by what the environment can actually support', () => {
  const bare = { admob: {}, play: {}, web: {} };
  assert.equal(MON.selectProvider(bare, {}), 'simulated');

  const play = { admob: {}, play: { enabled: true }, web: {} };
  assert.equal(MON.selectProvider(play, { hasDigitalGoods: true }), 'play');
  assert.equal(MON.selectProvider(play, { hasDigitalGoods: false }), 'simulated',
    'Play billing is never claimed where the API is absent');

  const web = { admob: {}, play: {}, web: { provider: 'flutterwave', publicKey: 'FLWPUBK-x' } };
  assert.equal(MON.selectProvider(web, {}), 'web');

  const ads = { admob: { rewardedUnitId: 'ca-app-pub-1/2' }, play: {}, web: {} };
  assert.equal(MON.selectProvider(ads, { hasAdMobBridge: true }), 'admob');
});

test('the shipped config is safe: simulated, test ads, no real charges', () => {
  assert.equal(MON.CONFIG.admob.testMode, true, 'test ads until the app is live');
  assert.equal(MON.CONFIG.play.enabled, false);
  assert.equal(MON.CONFIG.web.publicKey, '', 'no key committed to the repo');
  const live = MON.isLive(MON.CONFIG);
  assert.equal(live.any, false, 'nothing charges money until IDs are pasted in');
});

test('isLive reports exactly which revenue streams are switched on', () => {
  assert.deepEqual(
    MON.isLive({ admob: { rewardedUnitId: 'x', testMode: false }, play: {}, web: {} }),
    { ads: true, iap: false, any: true });
  assert.deepEqual(
    MON.isLive({ admob: { rewardedUnitId: 'x', testMode: true }, play: {}, web: {} }),
    { ads: false, iap: false, any: false }, 'test-mode ads earn nothing');
  assert.deepEqual(
    MON.isLive({ admob: {}, play: { enabled: true }, web: {} }),
    { ads: false, iap: true, any: true });
});

test('a simulated purchase completes and reports revenue events', () => {
  const seen = [];
  const off = MON.onEvent((e) => seen.push(e.type));
  let got = null;
  MON.purchase('coins_500', (p) => { got = p; });
  off();
  assert.equal(got.coins, 500);
  assert.deepEqual(seen, ['purchase_started', 'purchase_completed']);
});

test('an unknown product fails cleanly instead of granting anything', () => {
  let failed = null;
  let granted = false;
  MON.purchase('free_everything', () => { granted = true; }, (r) => { failed = r; });
  assert.equal(granted, false);
  assert.equal(failed, 'unknown_product');
});

test('a rewarded ad grants its reward and records the placement', () => {
  const seen = [];
  const off = MON.onEvent((e) => seen.push(e));
  let rewarded = false;
  MON.rewardedAd('continue', () => { rewarded = true; });
  off();
  assert.equal(rewarded, true);
  assert.equal(seen[0].placement, 'continue', 'placement is reported for revenue analysis');
  assert.ok(seen.some((e) => e.type === 'ad_rewarded'));
});

console.log('\n' + passed + ' tests passed' + (process.exitCode ? ' (with failures)' : ''));
