/*
 * Nairobi Wild — animal voices
 *
 * When a herd matches, that animal calls. Every call is synthesised at
 * runtime from oscillators and filtered noise — there is still not one
 * audio file in the build.
 *
 * The design is split in two so it can be tested:
 *   voiceSpec(colour)  — a pure DATA description of the call
 *   AnimalVoices.play() — turns a spec into WebAudio nodes
 *
 * A spec is a short sequence of pulses. Each pulse sweeps a tone from f0
 * to f1 while a noise bed and a moving filter shape the timbre:
 *
 *   Simba (lion)       a low sawtooth falling 150→55 Hz with a 24 Hz
 *                      rumble — the tremolo is what makes a roar read as
 *                      a roar rather than a groan.
 *   Tembo (elephant)   a bright rising trumpet, band-passed so it blares.
 *   Punda Milia (zebra) two short barks; a zebra's call is a double bark,
 *                      not a horse's whinny.
 *   Twiga (giraffe)    a 92 Hz hum. Giraffes really do hum at around this
 *                      pitch at night — it is the one call they have.
 *   Kifaru (rhino)     a noise-dominant snort with almost no pitch.
 *   Chui (leopard)     the sawing call: five rasping pulses in a row.
 *
 * Calls are kept short and quiet on purpose. They fire on every match, so
 * anything long or loud would be unbearable inside a minute.
 */
(function (global) {
  'use strict';

  const SPECS = [
    { // 0 — Simba, lion
      name: 'Simba', gain: 0.5, pulses: 1, pulseDur: 0.85, gap: 0,
      type: 'sawtooth', f0: 150, f1: 55,
      noise: 0.34, noiseFilter: 'lowpass', noiseFreq: 780,
      filterFrom: 900, filterTo: 260,
      tremoloRate: 24, tremoloDepth: 0.34,
      attack: 0.05,
    },
    { // 1 — Tembo, elephant
      name: 'Tembo', gain: 0.34, pulses: 1, pulseDur: 0.62, gap: 0,
      type: 'sawtooth', f0: 300, f1: 660,
      noise: 0.1, noiseFilter: 'bandpass', noiseFreq: 1500,
      filterFrom: 700, filterTo: 2200,
      tremoloRate: 0, tremoloDepth: 0,
      attack: 0.03,
    },
    { // 2 — Punda Milia, zebra
      name: 'Punda Milia', gain: 0.32, pulses: 2, pulseDur: 0.12, gap: 0.1,
      type: 'square', f0: 430, f1: 170,
      noise: 0.4, noiseFilter: 'bandpass', noiseFreq: 1100,
      filterFrom: 1800, filterTo: 500,
      tremoloRate: 0, tremoloDepth: 0,
      attack: 0.005,
    },
    { // 3 — Twiga, giraffe
      name: 'Twiga', gain: 0.36, pulses: 1, pulseDur: 0.7, gap: 0,
      type: 'sine', f0: 92, f1: 88,
      noise: 0.05, noiseFilter: 'lowpass', noiseFreq: 300,
      filterFrom: 260, filterTo: 190,
      tremoloRate: 6, tremoloDepth: 0.16,
      attack: 0.09,
    },
    { // 4 — Kifaru, rhino
      name: 'Kifaru', gain: 0.4, pulses: 1, pulseDur: 0.26, gap: 0,
      type: 'triangle', f0: 105, f1: 70,
      noise: 0.8, noiseFilter: 'lowpass', noiseFreq: 620,
      filterFrom: 700, filterTo: 300,
      tremoloRate: 0, tremoloDepth: 0,
      attack: 0.008,
    },
    { // 5 — Chui, leopard
      name: 'Chui', gain: 0.3, pulses: 5, pulseDur: 0.1, gap: 0.075,
      type: 'sawtooth', f0: 118, f1: 88,
      noise: 0.55, noiseFilter: 'bandpass', noiseFreq: 900,
      filterFrom: 800, filterTo: 340,
      tremoloRate: 0, tremoloDepth: 0,
      attack: 0.01,
    },
  ];

  function voiceSpec(color) {
    return SPECS[((color % SPECS.length) + SPECS.length) % SPECS.length];
  }

  /* When each pulse of a call starts, relative to the call's own start. */
  function pulseTimes(spec) {
    const out = [];
    for (let i = 0; i < spec.pulses; i += 1) out.push(i * (spec.pulseDur + spec.gap));
    return out;
  }

  function totalDuration(spec) {
    const t = pulseTimes(spec);
    return t[t.length - 1] + spec.pulseDur;
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
    this.volume = 0.9;
    this.enabled = true;
    this._last = 0;
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

    const amp = ctx.createGain();
    amp.gain.setValueAtTime(0.0001, t);
    amp.gain.exponentialRampToValueAtTime(spec.gain, t + spec.attack);
    amp.gain.exponentialRampToValueAtTime(0.0001, t + dur);

    const shaper = ctx.createBiquadFilter();
    shaper.type = 'lowpass';
    shaper.frequency.setValueAtTime(spec.filterFrom, t);
    shaper.frequency.exponentialRampToValueAtTime(Math.max(60, spec.filterTo), t + dur);
    shaper.Q.value = 3;
    shaper.connect(amp);
    amp.connect(this.master);

    // Tone: the pitch sweep is the call's shape.
    const osc = ctx.createOscillator();
    osc.type = spec.type;
    osc.frequency.setValueAtTime(spec.f0 * bend, t);
    osc.frequency.exponentialRampToValueAtTime(Math.max(20, spec.f1 * bend), t + dur);
    osc.connect(shaper);
    osc.start(t);
    osc.stop(t + dur + 0.02);

    // A roar is a rumble: amplitude modulation at ~24 Hz.
    if (spec.tremoloDepth > 0) {
      const lfo = ctx.createOscillator();
      const lfoGain = ctx.createGain();
      lfo.frequency.value = spec.tremoloRate;
      lfoGain.gain.value = spec.tremoloDepth * spec.gain;
      lfo.connect(lfoGain).connect(amp.gain);
      lfo.start(t);
      lfo.stop(t + dur + 0.02);
    }

    // Noise bed: breath, rasp and snort live here.
    if (spec.noise > 0) {
      const src = ctx.createBufferSource();
      src.buffer = this.noise;
      const nf = ctx.createBiquadFilter();
      nf.type = spec.noiseFilter;
      nf.frequency.value = spec.noiseFreq * bend;
      nf.Q.value = 1.1;
      const ng = ctx.createGain();
      ng.gain.setValueAtTime(0.0001, t);
      ng.gain.exponentialRampToValueAtTime(spec.noise * spec.gain, t + spec.attack);
      ng.gain.exponentialRampToValueAtTime(0.0001, t + dur);
      src.connect(nf).connect(ng).connect(this.master);
      src.start(t);
      src.stop(t + dur + 0.02);
    }
  };

  /*
   * Sound the call for a matched animal.
   * opts.combo lifts the pitch slightly as a cascade builds, so a long
   * chain rises instead of repeating flat.
   */
  AnimalVoices.prototype.play = function (color, opts) {
    if (!this.enabled || !this.ctx || !this.master) return;
    const now = this.ctx.currentTime;
    // Never stack more than a few calls a second, however fast the cascade.
    if (now - this._last < 0.07) return;
    this._last = now;

    const spec = voiceSpec(color);
    const combo = (opts && opts.combo) || 1;
    const semis = Math.min(6, (combo - 1) * 1.5) + (Math.random() * 1.2 - 0.6);
    try {
      pulseTimes(spec).forEach((offset) => this._pulse(spec, now + 0.01 + offset, semis));
    } catch (e) { /* audio can fail on locked-down devices; play on regardless */ }
  };

  AnimalVoices.prototype.setVolume = function (v) {
    this.volume = v;
    if (this.master && this.ctx) this.master.gain.setTargetAtTime(v, this.ctx.currentTime, 0.05);
  };

  const Sounds = { SPECS, voiceSpec, pulseTimes, totalDuration, AnimalVoices };

  if (typeof module !== 'undefined' && module.exports) module.exports = Sounds;
  else global.AnimalSounds = Sounds;
})(typeof window !== 'undefined' ? window : globalThis);
