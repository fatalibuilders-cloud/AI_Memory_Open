/*
 * Nairobi Wild — animal voices
 *
 * When a herd matches, that animal calls. Every call is synthesised at
 * runtime; there is still not one audio file in the build.
 *
 * WHY THIS IS BUILT THE WAY IT IS
 * A single oscillator swept through a low-pass does not sound like an
 * animal — it sounds like a buzz. Two things fix that, and both are here:
 *
 *  1. HARMONIC STACK. Real calls are rich. Each voice sums several
 *     partials (multiples of the fundamental), so the ear hears a voice
 *     rather than a test tone.
 *  2. FORMANTS. An animal's throat and mouth resonate at fixed
 *     frequencies regardless of pitch. A parallel bank of narrow
 *     band-passes reproduces that, and it is what makes a roar read as a
 *     roar rather than a low hum.
 *
 * PHONE SPEAKERS. A phone cannot reproduce much below ~300 Hz. A lion's
 * real fundamental is far below that, so a "accurate" 55 Hz roar is
 * silent on the device most players will use. Every voice here therefore
 * carries its character in partials and formants inside roughly
 * 300–3000 Hz, where a phone speaker actually works, while keeping the
 * fundamental honest. A test asserts each call has audible energy in
 * that band.
 *
 * The design is split so it can be tested without audio hardware:
 *   voiceSpec(colour)   — pure DATA describing the call
 *   AnimalVoices.play() — turns a spec into WebAudio nodes
 */
(function (global) {
  'use strict';

  /*
   * partials: multiples of the fundamental — [multiple, gain, wave]
   * formants: fixed throat resonances — {freq, q, gain}
   * am:       amplitude roughness; a growl is a fast, deep tremolo
   * noise:    breath, rasp, snort — a band-passed noise bed that sweeps
   */
  const SPECS = [
    { // 0 — Simba, the lion: a long roar with a heavy growl
      name: 'Simba', gain: 0.55, pulses: 1, pulseDur: 1.0, gap: 0,
      f0: 200, f1: 75,
      partials: [[1, 1.0, 'sawtooth'], [2, 0.55, 'sawtooth'], [3, 0.3, 'triangle'], [4, 0.15, 'sine']],
      formants: [{ freq: 420, q: 5, gain: 1.0 }, { freq: 900, q: 6, gain: 0.65 }, { freq: 1850, q: 8, gain: 0.3 }],
      noise: { amount: 0.28, from: 950, to: 420, q: 1.1 },
      am: { rate: 28, depth: 0.45 },
      attack: 0.06,
    },
    { // 1 — Tembo, the elephant: a rising brass trumpet
      name: 'Tembo', gain: 0.42, pulses: 1, pulseDur: 0.72, gap: 0,
      f0: 380, f1: 800,
      partials: [[1, 1.0, 'sawtooth'], [2, 0.6, 'sawtooth'], [3, 0.35, 'square'], [4, 0.16, 'sawtooth']],
      formants: [{ freq: 1150, q: 7, gain: 1.0 }, { freq: 2100, q: 8, gain: 0.55 }],
      noise: { amount: 0.12, from: 1800, to: 3000, q: 1.4 },
      am: { rate: 0, depth: 0 },
      attack: 0.02,
    },
    { // 2 — Punda Milia, the zebra: two sharp barks, not a whinny
      name: 'Punda Milia', gain: 0.46, pulses: 2, pulseDur: 0.14, gap: 0.09,
      f0: 520, f1: 200,
      partials: [[1, 1.0, 'sawtooth'], [2, 0.5, 'square']],
      formants: [{ freq: 720, q: 4, gain: 1.0 }, { freq: 1600, q: 6, gain: 0.55 }],
      noise: { amount: 0.5, from: 1800, to: 700, q: 1.0 },
      am: { rate: 0, depth: 0 },
      attack: 0.004,
    },
    { // 3 — Twiga, the giraffe: the 92 Hz night hum, voiced so a phone
      //     can carry it — the fundamental stays honest, the harmonics
      //     do the work.
      name: 'Twiga', gain: 0.5, pulses: 1, pulseDur: 0.8, gap: 0,
      f0: 92, f1: 88,
      partials: [[1, 0.9, 'sine'], [2, 0.8, 'sine'], [3, 0.6, 'triangle'], [5, 0.3, 'sine'], [7, 0.15, 'sine']],
      formants: [{ freq: 300, q: 4, gain: 1.0 }, { freq: 580, q: 5, gain: 0.6 }, { freq: 1000, q: 6, gain: 0.25 }],
      noise: { amount: 0.07, from: 500, to: 350, q: 1.2 },
      am: { rate: 7, depth: 0.22 },
      attack: 0.1,
    },
    { // 4 — Kifaru, the rhino: a double snort, mostly breath
      name: 'Kifaru', gain: 0.5, pulses: 2, pulseDur: 0.16, gap: 0.06,
      f0: 170, f1: 95,
      partials: [[1, 0.8, 'sawtooth'], [2, 0.45, 'sawtooth'], [3, 0.2, 'triangle']],
      formants: [{ freq: 430, q: 3, gain: 1.0 }, { freq: 980, q: 4, gain: 0.65 }],
      noise: { amount: 0.85, from: 1300, to: 380, q: 1.2 },
      am: { rate: 0, depth: 0 },
      attack: 0.006,
    },
    { // 5 — Chui, the leopard: the sawing call, five rasping strokes
      name: 'Chui', gain: 0.44, pulses: 5, pulseDur: 0.11, gap: 0.07,
      f0: 210, f1: 145,
      partials: [[1, 1.0, 'sawtooth'], [2, 0.55, 'sawtooth'], [3, 0.28, 'sawtooth']],
      formants: [{ freq: 620, q: 5, gain: 1.0 }, { freq: 1300, q: 6, gain: 0.55 }],
      noise: { amount: 0.6, from: 1500, to: 520, q: 1.1 },
      am: { rate: 45, depth: 0.5 },
      attack: 0.012,
    },
  ];

  function voiceSpec(color) {
    return SPECS[((color % SPECS.length) + SPECS.length) % SPECS.length];
  }

  function pulseTimes(spec) {
    const out = [];
    for (let i = 0; i < spec.pulses; i += 1) out.push(i * (spec.pulseDur + spec.gap));
    return out;
  }

  function totalDuration(spec) {
    const t = pulseTimes(spec);
    return t[t.length - 1] + spec.pulseDur;
  }

  /*
   * The highest frequency the voice puts real energy into — the check
   * that decides whether a phone speaker can carry the call at all.
   * Formants resonate regardless of pitch, so they count too.
   */
  function topAudibleFreq(spec) {
    const highestPartial = Math.max(...spec.partials.map((p) => p[0])) * Math.max(spec.f0, spec.f1);
    const highestFormant = Math.max(...spec.formants.map((f) => f.freq));
    return Math.max(highestPartial, highestFormant);
  }

  function makeNoiseBuffer(ctx) {
    const len = Math.floor(ctx.sampleRate * 1.2);
    const buf = ctx.createBuffer(1, len, ctx.sampleRate);
    const d = buf.getChannelData(0);
    for (let i = 0; i < len; i += 1) d[i] = Math.random() * 2 - 1;
    return buf;
  }

  function AnimalVoices() {
    this.ctx = null;
    this.master = null;
    this.noise = null;
    this.volume = 1.0;
    this.enabled = true;
    this._last = -1;          // so the very first call is never suppressed
    this.onPlay = null;       // the game uses this to duck the music
  }

  AnimalVoices.prototype.attach = function (ctx, destination) {
    if (!ctx) return;
    this.ctx = ctx;
    this.master = ctx.createGain();
    this.master.gain.value = this.volume;
    this.master.connect(destination || ctx.destination);
    this.noise = makeNoiseBuffer(ctx);
  };

  AnimalVoices.prototype._pulse = function (spec, t, semitones) {
    const ctx = this.ctx;
    const bend = Math.pow(2, (semitones || 0) / 12);
    const dur = spec.pulseDur;
    const f0 = spec.f0 * bend;
    const f1 = Math.max(20, spec.f1 * bend);

    // One envelope for the whole pulse.
    const amp = ctx.createGain();
    amp.gain.setValueAtTime(0.0001, t);
    amp.gain.exponentialRampToValueAtTime(spec.gain, t + spec.attack);
    amp.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    amp.connect(this.master);

    // A growl is amplitude roughness, not pitch — modulate the envelope.
    if (spec.am && spec.am.depth > 0) {
      const lfo = ctx.createOscillator();
      const lfoGain = ctx.createGain();
      lfo.type = 'sine';
      lfo.frequency.value = spec.am.rate;
      lfoGain.gain.value = spec.am.depth * spec.gain;
      lfo.connect(lfoGain);
      lfoGain.connect(amp.gain);
      lfo.start(t);
      lfo.stop(t + dur + 0.02);
    }

    // Parallel formant bank — the throat. This is what gives the call a body.
    const mix = ctx.createGain();
    mix.gain.value = 1;
    spec.formants.forEach((f) => {
      const bp = ctx.createBiquadFilter();
      bp.type = 'bandpass';
      bp.frequency.value = f.freq;
      bp.Q.value = f.q;
      const g = ctx.createGain();
      g.gain.value = f.gain;
      mix.connect(bp);
      bp.connect(g);
      g.connect(amp);
    });
    // A little dry signal keeps the attack crisp.
    const dry = ctx.createGain();
    dry.gain.value = 0.35;
    mix.connect(dry);
    dry.connect(amp);

    // Harmonic stack — the voice.
    spec.partials.forEach(([mult, gain, wave]) => {
      const o = ctx.createOscillator();
      o.type = wave;
      o.frequency.setValueAtTime(f0 * mult, t);
      o.frequency.exponentialRampToValueAtTime(Math.max(20, f1 * mult), t + dur);
      const g = ctx.createGain();
      g.gain.value = gain;
      o.connect(g);
      g.connect(mix);
      o.start(t);
      o.stop(t + dur + 0.02);
    });

    // Breath / rasp / snort.
    if (spec.noise && spec.noise.amount > 0) {
      const src = ctx.createBufferSource();
      src.buffer = this.noise;
      const nf = ctx.createBiquadFilter();
      nf.type = 'bandpass';
      nf.frequency.setValueAtTime(spec.noise.from, t);
      nf.frequency.exponentialRampToValueAtTime(Math.max(60, spec.noise.to), t + dur);
      nf.Q.value = spec.noise.q;
      const ng = ctx.createGain();
      ng.gain.value = spec.noise.amount;
      src.connect(nf);
      nf.connect(ng);
      ng.connect(amp);
      src.start(t);
      src.stop(t + dur + 0.02);
    }
  };

  /*
   * Sound the call for a matched animal.
   * opts.combo lifts the pitch as a cascade builds, so a long chain rises
   * instead of repeating flat.
   */
  AnimalVoices.prototype.play = function (color, opts) {
    if (!this.enabled || !this.ctx || !this.master) return false;
    const now = this.ctx.currentTime;
    // Never stack more than a few calls a second, however fast the cascade.
    if (this._last >= 0 && now - this._last < 0.07) return false;
    this._last = now;

    const spec = voiceSpec(color);
    const combo = (opts && opts.combo) || 1;
    const semis = Math.min(6, (combo - 1) * 1.5) + (Math.random() * 1.2 - 0.6);
    try {
      pulseTimes(spec).forEach((offset) => this._pulse(spec, now + 0.01 + offset, semis));
      if (this.onPlay) this.onPlay(spec, totalDuration(spec));
      return true;
    } catch (e) {
      return false; // audio can fail on locked-down devices; play on regardless
    }
  };

  AnimalVoices.prototype.setVolume = function (v) {
    this.volume = v;
    if (this.master && this.ctx) this.master.gain.setTargetAtTime(v, this.ctx.currentTime, 0.05);
  };

  const Sounds = { SPECS, voiceSpec, pulseTimes, totalDuration, topAudibleFreq, AnimalVoices };

  if (typeof module !== 'undefined' && module.exports) module.exports = Sounds;
  else global.AnimalSounds = Sounds;
})(typeof window !== 'undefined' ? window : globalThis);
