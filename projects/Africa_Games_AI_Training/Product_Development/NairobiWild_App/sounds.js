/*
 * Nairobi Wild — animal voices
 *
 * Every call is synthesised at runtime; there is not one audio file in the
 * build. Voices are keyed by ARCHETYPE ('roar', 'trumpet', ...) rather than
 * by species, because the board's six animals change from country to
 * country — a Kenyan stage fields lions and rhinos, a Ugandan one gorillas
 * and hippos — and many species share a manner of calling.
 *
 * WHY THIS IS BUILT THE WAY IT IS
 * A single oscillator swept through a low-pass is a buzz, not an animal.
 * Two things fix that and both are in every voice:
 *   1. HARMONIC STACK — several partials, so the ear hears a voice.
 *   2. FORMANTS — a parallel bank of narrow band-passes standing in for
 *      the throat, which resonates at fixed frequencies whatever the pitch.
 *      This is what gives a roar its body.
 *
 * PHONE SPEAKERS SET THE DESIGN. A phone reproduces almost nothing below
 * ~300 Hz, so a zoologically "correct" 55 Hz lion roar is silent on the
 * device most players use. Every voice keeps an honest fundamental but
 * carries its character in partials and formants inside ~300-3000 Hz.
 * A test asserts each call reaches that band.
 *
 * Split so it can be tested without audio hardware:
 *   voiceFor(key)       — pure DATA describing the call
 *   AnimalVoices.play() — turns it into WebAudio nodes
 */
(function (global) {
  'use strict';

  /*
   * partials: [multiple of fundamental, gain, waveform]
   * formants: {freq, q, gain} — fixed throat resonances
   * am:       amplitude roughness; a growl is a fast, deep tremolo
   * noise:    breath, rasp, snort — band-passed noise that sweeps
   */
  const VOICES = {
    roar: { // lion
      label: 'roar', gain: 0.6, pulses: 1, pulseDur: 1.0, gap: 0, attack: 0.06,
      f0: 200, f1: 75,
      partials: [[1, 1.0, 'sawtooth'], [2, 0.55, 'sawtooth'], [3, 0.3, 'triangle'], [4, 0.15, 'sine']],
      formants: [{ freq: 420, q: 5, gain: 1.0 }, { freq: 900, q: 6, gain: 0.65 }, { freq: 1850, q: 8, gain: 0.3 }],
      noise: { amount: 0.28, from: 950, to: 420, q: 1.1 },
      am: { rate: 28, depth: 0.45 },
    },
    trumpet: { // elephant
      label: 'trumpet', gain: 0.5, pulses: 1, pulseDur: 0.72, gap: 0, attack: 0.02,
      f0: 380, f1: 800,
      partials: [[1, 1.0, 'sawtooth'], [2, 0.6, 'sawtooth'], [3, 0.35, 'square'], [4, 0.16, 'sawtooth']],
      formants: [{ freq: 1150, q: 7, gain: 1.0 }, { freq: 2100, q: 8, gain: 0.55 }],
      noise: { amount: 0.12, from: 1800, to: 3000, q: 1.4 },
      am: { rate: 0, depth: 0 },
    },
    bark: { // zebra, wild dog, baboon
      label: 'bark', gain: 0.52, pulses: 2, pulseDur: 0.2, gap: 0.12, attack: 0.004,
      f0: 520, f1: 200,
      partials: [[1, 1.0, 'sawtooth'], [2, 0.5, 'square']],
      formants: [{ freq: 720, q: 4, gain: 1.0 }, { freq: 1600, q: 6, gain: 0.55 }],
      noise: { amount: 0.5, from: 1800, to: 700, q: 1.0 },
      am: { rate: 0, depth: 0 },
    },
    hum: { // giraffe — the real 92 Hz night hum, voiced so a phone carries it
      label: 'hum', gain: 0.55, pulses: 1, pulseDur: 0.8, gap: 0, attack: 0.1,
      f0: 92, f1: 88,
      partials: [[1, 0.9, 'sine'], [2, 0.8, 'sine'], [3, 0.6, 'triangle'], [5, 0.3, 'sine'], [7, 0.15, 'sine']],
      formants: [{ freq: 300, q: 4, gain: 1.0 }, { freq: 580, q: 5, gain: 0.6 }, { freq: 1000, q: 6, gain: 0.25 }],
      noise: { amount: 0.07, from: 500, to: 350, q: 1.2 },
      am: { rate: 7, depth: 0.22 },
    },
    snort: { // rhino, warthog
      label: 'snort', gain: 0.56, pulses: 2, pulseDur: 0.22, gap: 0.1, attack: 0.006,
      f0: 170, f1: 95,
      partials: [[1, 0.8, 'sawtooth'], [2, 0.45, 'sawtooth'], [3, 0.2, 'triangle']],
      formants: [{ freq: 430, q: 3, gain: 1.0 }, { freq: 980, q: 4, gain: 0.65 }],
      noise: { amount: 0.85, from: 1300, to: 380, q: 1.2 },
      am: { rate: 0, depth: 0 },
    },
    rasp: { // leopard, cheetah — the sawing call
      label: 'sawing call', gain: 0.5, pulses: 5, pulseDur: 0.11, gap: 0.07, attack: 0.012,
      f0: 210, f1: 145,
      partials: [[1, 1.0, 'sawtooth'], [2, 0.55, 'sawtooth'], [3, 0.28, 'sawtooth']],
      formants: [{ freq: 620, q: 5, gain: 1.0 }, { freq: 1300, q: 6, gain: 0.55 }],
      noise: { amount: 0.6, from: 1500, to: 520, q: 1.1 },
      am: { rate: 45, depth: 0.5 },
    },
    bellow: { // buffalo, cattle
      label: 'bellow', gain: 0.56, pulses: 1, pulseDur: 0.85, gap: 0, attack: 0.05,
      f0: 150, f1: 105,
      partials: [[1, 1.0, 'sawtooth'], [2, 0.7, 'sawtooth'], [3, 0.4, 'triangle'], [5, 0.15, 'sine']],
      formants: [{ freq: 480, q: 4, gain: 1.0 }, { freq: 1100, q: 5, gain: 0.5 }],
      noise: { amount: 0.3, from: 900, to: 500, q: 1.0 },
      am: { rate: 12, depth: 0.25 },
    },
    grunt: { // hippo — the deep honking grunt
      label: 'grunt', gain: 0.58, pulses: 3, pulseDur: 0.18, gap: 0.08, attack: 0.01,
      f0: 130, f1: 90,
      partials: [[1, 1.0, 'square'], [2, 0.6, 'sawtooth'], [3, 0.35, 'sawtooth'], [4, 0.18, 'triangle']],
      formants: [{ freq: 380, q: 4, gain: 1.0 }, { freq: 820, q: 5, gain: 0.6 }, { freq: 1500, q: 7, gain: 0.25 }],
      noise: { amount: 0.35, from: 1000, to: 400, q: 1.1 },
      am: { rate: 18, depth: 0.3 },
    },
    hoot: { // gorilla, chimpanzee — the rising pant-hoot
      label: 'hoot', gain: 0.5, pulses: 3, pulseDur: 0.16, gap: 0.07, attack: 0.02,
      f0: 300, f1: 520,
      partials: [[1, 1.0, 'sine'], [2, 0.55, 'triangle'], [3, 0.25, 'sine']],
      formants: [{ freq: 700, q: 6, gain: 1.0 }, { freq: 1400, q: 7, gain: 0.45 }],
      noise: { amount: 0.2, from: 1200, to: 800, q: 1.3 },
      am: { rate: 0, depth: 0 },
    },
    chatter: { // monkey, lemur
      label: 'chatter', gain: 0.44, pulses: 5, pulseDur: 0.07, gap: 0.045, attack: 0.004,
      f0: 800, f1: 520,
      partials: [[1, 1.0, 'square'], [2, 0.45, 'sawtooth']],
      formants: [{ freq: 1300, q: 6, gain: 1.0 }, { freq: 2400, q: 7, gain: 0.5 }],
      noise: { amount: 0.35, from: 2600, to: 1200, q: 1.2 },
      am: { rate: 0, depth: 0 },
    },
    whoop: { // hyena — the rising whoop
      label: 'whoop', gain: 0.5, pulses: 2, pulseDur: 0.34, gap: 0.1, attack: 0.03,
      f0: 260, f1: 620,
      partials: [[1, 1.0, 'sine'], [2, 0.5, 'triangle'], [3, 0.2, 'sine']],
      formants: [{ freq: 780, q: 6, gain: 1.0 }, { freq: 1600, q: 7, gain: 0.4 }],
      noise: { amount: 0.18, from: 1400, to: 900, q: 1.3 },
      am: { rate: 0, depth: 0 },
    },
    hiss: { // crocodile, snake, chameleon
      label: 'hiss', gain: 0.46, pulses: 1, pulseDur: 0.55, gap: 0, attack: 0.03,
      f0: 240, f1: 180,
      partials: [[1, 0.4, 'sawtooth'], [2, 0.2, 'triangle']],
      formants: [{ freq: 1600, q: 3, gain: 1.0 }, { freq: 3000, q: 4, gain: 0.6 }],
      noise: { amount: 0.95, from: 2600, to: 1400, q: 0.9 },
      am: { rate: 9, depth: 0.2 },
    },
    bleat: { // antelope, gazelle, goat, camel
      label: 'bleat', gain: 0.48, pulses: 2, pulseDur: 0.23, gap: 0.09, attack: 0.015,
      f0: 380, f1: 300,
      partials: [[1, 1.0, 'sawtooth'], [2, 0.55, 'triangle'], [3, 0.25, 'sine']],
      formants: [{ freq: 900, q: 5, gain: 1.0 }, { freq: 1800, q: 6, gain: 0.45 }],
      noise: { amount: 0.25, from: 1600, to: 900, q: 1.2 },
      am: { rate: 22, depth: 0.35 },
    },
    honk: { // flamingo, crane, pelican
      label: 'honk', gain: 0.46, pulses: 2, pulseDur: 0.22, gap: 0.1, attack: 0.012,
      f0: 460, f1: 380,
      partials: [[1, 1.0, 'sawtooth'], [2, 0.6, 'square'], [3, 0.28, 'sawtooth']],
      formants: [{ freq: 1000, q: 5, gain: 1.0 }, { freq: 2000, q: 6, gain: 0.5 }],
      noise: { amount: 0.3, from: 2200, to: 1100, q: 1.2 },
      am: { rate: 14, depth: 0.25 },
    },
    screech: { // eagle, falcon
      label: 'screech', gain: 0.42, pulses: 3, pulseDur: 0.13, gap: 0.06, attack: 0.006,
      f0: 1200, f1: 780,
      partials: [[1, 1.0, 'sawtooth'], [2, 0.4, 'square']],
      formants: [{ freq: 2200, q: 6, gain: 1.0 }, { freq: 3200, q: 7, gain: 0.5 }],
      noise: { amount: 0.4, from: 3400, to: 1800, q: 1.1 },
      am: { rate: 0, depth: 0 },
    },
    squawk: { // parrot
      label: 'squawk', gain: 0.44, pulses: 2, pulseDur: 0.2, gap: 0.1, attack: 0.005,
      f0: 900, f1: 600,
      partials: [[1, 1.0, 'square'], [2, 0.5, 'sawtooth'], [3, 0.2, 'sawtooth']],
      formants: [{ freq: 1500, q: 5, gain: 1.0 }, { freq: 2800, q: 6, gain: 0.5 }],
      noise: { amount: 0.45, from: 3000, to: 1400, q: 1.1 },
      am: { rate: 30, depth: 0.3 },
    },
    bray: { // penguin (the African penguin is nicknamed the jackass penguin)
      label: 'bray', gain: 0.48, pulses: 2, pulseDur: 0.26, gap: 0.09, attack: 0.02,
      f0: 300, f1: 200,
      partials: [[1, 1.0, 'sawtooth'], [2, 0.6, 'sawtooth'], [3, 0.3, 'square']],
      formants: [{ freq: 850, q: 5, gain: 1.0 }, { freq: 1700, q: 6, gain: 0.45 }],
      noise: { amount: 0.4, from: 1800, to: 800, q: 1.1 },
      am: { rate: 20, depth: 0.4 },
    },
    yelp: { // fennec fox, jackal
      label: 'yelp', gain: 0.44, pulses: 3, pulseDur: 0.13, gap: 0.07, attack: 0.005,
      f0: 700, f1: 420,
      partials: [[1, 1.0, 'sawtooth'], [2, 0.45, 'triangle']],
      formants: [{ freq: 1200, q: 5, gain: 1.0 }, { freq: 2300, q: 6, gain: 0.45 }],
      noise: { amount: 0.3, from: 2400, to: 1100, q: 1.2 },
      am: { rate: 0, depth: 0 },
    },
    splash: { // fish, turtle, dolphin — a watery flip, mostly noise
      label: 'splash', gain: 0.42, pulses: 1, pulseDur: 0.45, gap: 0, attack: 0.004,
      f0: 500, f1: 260,
      partials: [[1, 0.35, 'sine'], [2, 0.2, 'triangle']],
      formants: [{ freq: 1400, q: 2.5, gain: 1.0 }, { freq: 2600, q: 3, gain: 0.5 }],
      noise: { amount: 0.9, from: 3200, to: 700, q: 0.8 },
      am: { rate: 0, depth: 0 },
    },
  };

  const VOICE_KEYS = Object.keys(VOICES);

  function voiceFor(key) {
    return VOICES[key] || VOICES.roar;
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
   * The highest frequency the voice puts real energy into — the check that
   * decides whether a phone speaker can carry the call at all. Formants
   * resonate regardless of pitch, so they count.
   */
  function topAudibleFreq(spec) {
    const highestPartial = Math.max.apply(null, spec.partials.map((p) => p[0])) * Math.max(spec.f0, spec.f1);
    const highestFormant = Math.max.apply(null, spec.formants.map((f) => f.freq));
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
    this.volume = 1.6;      // calls sit above the music, not under it
    this.enabled = true;
    this._last = -1;        // so the very first call is never suppressed
    this.onPlay = null;     // the game uses this to duck the music
  }

  AnimalVoices.prototype.attach = function (ctx, destination) {
    if (!ctx) return false;
    this.ctx = ctx;
    this.master = ctx.createGain();
    this.master.gain.value = this.volume;
    this.master.connect(destination || ctx.destination);
    this.noise = makeNoiseBuffer(ctx);
    return true;
  };

  AnimalVoices.prototype._pulse = function (spec, t, semitones) {
    const ctx = this.ctx;
    const bend = Math.pow(2, (semitones || 0) / 12);
    const dur = spec.pulseDur;
    const f0 = spec.f0 * bend;
    const f1 = Math.max(20, spec.f1 * bend);

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
    const dry = ctx.createGain();   // keeps the attack crisp
    dry.gain.value = 0.35;
    mix.connect(dry);
    dry.connect(amp);

    // Harmonic stack — the voice.
    spec.partials.forEach(function (p) {
      const o = ctx.createOscillator();
      o.type = p[2];
      o.frequency.setValueAtTime(f0 * p[0], t);
      o.frequency.exponentialRampToValueAtTime(Math.max(20, f1 * p[0]), t + dur);
      const g = ctx.createGain();
      g.gain.value = p[1];
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
   * Sound a call. `key` is a voice archetype ('roar', 'trumpet', ...).
   * opts.combo lifts the pitch as a cascade builds.
   * Returns true only if audio was really scheduled, so the UI can tell
   * the player when sound is unavailable instead of failing silently.
   */
  AnimalVoices.prototype.play = function (key, opts) {
    if (!this.enabled || !this.ctx || !this.master) return false;
    if (this.ctx.state === 'suspended') {
      try { this.ctx.resume(); } catch (e) { /* fall through and try anyway */ }
    }
    const now = this.ctx.currentTime;
    if (this._last >= 0 && now - this._last < 0.07) return false;
    this._last = now;

    const spec = voiceFor(key);
    const combo = (opts && opts.combo) || 1;
    const semis = Math.min(6, (combo - 1) * 1.5) + (Math.random() * 1.2 - 0.6);
    try {
      const self = this;
      pulseTimes(spec).forEach(function (offset) { self._pulse(spec, now + 0.01 + offset, semis); });
      if (this.onPlay) this.onPlay(spec, totalDuration(spec));
      return true;
    } catch (e) {
      return false;
    }
  };

  AnimalVoices.prototype.setVolume = function (v) {
    this.volume = v;
    if (this.master && this.ctx) this.master.gain.setTargetAtTime(v, this.ctx.currentTime, 0.05);
  };

  const Sounds = { VOICES, VOICE_KEYS, voiceFor, pulseTimes, totalDuration, topAudibleFreq, AnimalVoices };

  if (typeof module !== 'undefined' && module.exports) module.exports = Sounds;
  else global.AnimalSounds = Sounds;
})(typeof window !== 'undefined' ? window : globalThis);
