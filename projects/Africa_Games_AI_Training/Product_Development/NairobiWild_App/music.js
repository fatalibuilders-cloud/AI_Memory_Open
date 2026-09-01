/*
 * Nairobi Wild — generative Afro soundtrack
 *
 * Every sound in this game is synthesised at runtime. There is not one
 * audio file in the build, which is the whole point: a licensed music bed
 * would add megabytes to a game whose pitch is that it costs almost no data
 * to install, and would need clearing in every market we launch in.
 *
 * What it plays: a Benga-flavoured groove — the fast, guitar-led Kenyan
 * dance style out of Nairobi. Benga's signature is a bright, endlessly
 * cycling plucked riff (descended from nyatiti lyre playing) over a busy
 * bassline and a shaker pulse, so that is what the sequencer builds:
 *
 *   kick     — four-on-the-floor with a syncopated push
 *   shaker   — kayamba-style 16ths, accented off-beat
 *   clap     — backbeat on 2 and 4
 *   bass     — pentatonic root movement, one octave, round and short
 *   riff     — the Benga guitar/nyatiti line, plucked 8ths in F pentatonic
 *   marimba  — sparse high answer-phrases, layered in only at high energy
 *
 * Scheduling uses the standard WebAudio lookahead pattern: a 25 ms timer
 * schedules every note that falls inside the next 120 ms against the
 * AudioContext clock, so timing never drifts with the main thread.
 *
 * The pattern builders are pure functions exported for tests.
 */
(function (global) {
  'use strict';

  const BPM = 112;
  const STEPS = 16;                    // 16th notes per bar
  const BARS = 4;                      // riff cycles over 4 bars
  const SPB = 60 / BPM / 4;            // seconds per 16th step

  /* F minor pentatonic — the backbone of a great deal of East African
   * guitar music, and forgiving enough that random layering never clashes. */
  const SCALE = [174.61, 207.65, 233.08, 261.63, 311.13]; // F Ab Bb C Eb
  const ROOTS = [87.31, 87.31, 116.54, 103.83];           // F F Bb Ab, one per bar

  const on = (step, ...hits) => hits.includes(step);

  /* ---- pattern builders (pure, unit-tested) ---- */

  function kickPattern(bar) {
    const out = [];
    for (let s = 0; s < STEPS; s += 1) {
      // Four on the floor, plus a push before the turnaround.
      if (on(s, 0, 4, 8, 12) || (bar % 2 === 1 && on(s, 14))) out.push(s);
    }
    return out;
  }

  function shakerPattern() {
    const out = [];
    for (let s = 0; s < STEPS; s += 1) out.push(s); // kayamba runs 16ths
    return out;
  }

  function clapPattern() {
    return [4, 12]; // backbeat
  }

  function bassPattern(bar) {
    // Busy, round bass: root on the beat, a fifth-ish lift late in the bar.
    const root = ROOTS[bar % ROOTS.length];
    const notes = [];
    [0, 3, 6, 8, 11, 14].forEach((s, i) => {
      notes.push({ step: s, freq: i % 3 === 2 ? root * 1.5 : root });
    });
    return notes;
  }

  /*
   * The Benga riff: a cycling plucked figure that shifts one scale degree
   * each bar, so four bars feel like a phrase rather than a loop.
   */
  function riffPattern(bar) {
    const shape = [0, 2, 4, 2, 3, 1, 2, 0];     // scale degrees
    const steps = [0, 2, 4, 6, 8, 10, 12, 14];  // straight 8ths
    return steps.map((s, i) => {
      const deg = (shape[i] + bar) % SCALE.length;
      const octave = i >= 4 ? 2 : 1;
      return { step: s, freq: SCALE[deg] * octave };
    });
  }

  function marimbaPattern(bar) {
    // Sparse answering phrase, only on the back half of the cycle.
    if (bar % 2 === 0) return [];
    return [
      { step: 6,  freq: SCALE[(bar + 2) % SCALE.length] * 4 },
      { step: 10, freq: SCALE[(bar + 4) % SCALE.length] * 4 },
      { step: 13, freq: SCALE[(bar + 1) % SCALE.length] * 4 },
    ];
  }

  /* ---- voices ---- */

  function makeNoiseBuffer(ctx) {
    const len = Math.floor(ctx.sampleRate * 0.4);
    const buf = ctx.createBuffer(1, len, ctx.sampleRate);
    const d = buf.getChannelData(0);
    for (let i = 0; i < len; i += 1) d[i] = Math.random() * 2 - 1;
    return buf;
  }

  function Engine() {
    this.ctx = null;
    this.master = null;
    this.noise = null;
    this.timer = null;
    this.step = 0;
    this.bar = 0;
    this.nextTime = 0;
    this.playing = false;
    this.energy = 1;      // 0 menus · 1 play · 2 cascade heat
    this.volume = 0.55;
  }

  Engine.prototype._voiceKick = function (t) {
    const o = this.ctx.createOscillator();
    const g = this.ctx.createGain();
    o.type = 'sine';
    o.frequency.setValueAtTime(128, t);
    o.frequency.exponentialRampToValueAtTime(42, t + 0.11);
    g.gain.setValueAtTime(0.9, t);
    g.gain.exponentialRampToValueAtTime(0.001, t + 0.22);
    o.connect(g).connect(this.master);
    o.start(t); o.stop(t + 0.24);
  };

  Engine.prototype._voiceNoise = function (t, { dur, freq, q, gain, type }) {
    const src = this.ctx.createBufferSource();
    src.buffer = this.noise;
    const f = this.ctx.createBiquadFilter();
    f.type = type || 'bandpass';
    f.frequency.value = freq;
    f.Q.value = q || 1;
    const g = this.ctx.createGain();
    g.gain.setValueAtTime(gain, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    src.connect(f).connect(g).connect(this.master);
    src.start(t); src.stop(t + dur + 0.02);
  };

  Engine.prototype._voiceBass = function (t, freq) {
    const o = this.ctx.createOscillator();
    const f = this.ctx.createBiquadFilter();
    const g = this.ctx.createGain();
    o.type = 'triangle';
    o.frequency.setValueAtTime(freq, t);
    f.type = 'lowpass'; f.frequency.value = 480;
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(0.5, t + 0.012);
    g.gain.exponentialRampToValueAtTime(0.0001, t + 0.19);
    o.connect(f).connect(g).connect(this.master);
    o.start(t); o.stop(t + 0.21);
  };

  /* Plucked string — two detuned triangles with a fast decay reads as a
   * nyatiti/Benga guitar far better than a single sine. */
  Engine.prototype._voicePluck = function (t, freq, gain) {
    const g = this.ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(gain, t + 0.008);
    g.gain.exponentialRampToValueAtTime(0.0001, t + 0.3);
    const f = this.ctx.createBiquadFilter();
    f.type = 'lowpass'; f.frequency.value = 2600;
    [0, 1.004].forEach((detune, i) => {
      const o = this.ctx.createOscillator();
      o.type = i === 0 ? 'triangle' : 'sine';
      o.frequency.value = freq * detune;
      o.connect(f);
      o.start(t); o.stop(t + 0.32);
    });
    f.connect(g).connect(this.master);
  };

  Engine.prototype._scheduleStep = function (step, bar, t) {
    const e = this.energy;
    if (kickPattern(bar).includes(step)) this._voiceKick(t);
    if (shakerPattern().includes(step)) {
      const accent = step % 2 === 1;
      this._voiceNoise(t, { dur: 0.045, freq: 7200, q: 0.8, gain: accent ? 0.075 : 0.035, type: 'highpass' });
    }
    if (clapPattern().includes(step)) {
      this._voiceNoise(t, { dur: 0.1, freq: 1700, q: 1.2, gain: 0.2 });
    }
    if (e >= 1) {
      bassPattern(bar).forEach((n) => { if (n.step === step) this._voiceBass(t, n.freq); });
      riffPattern(bar).forEach((n) => { if (n.step === step) this._voicePluck(t, n.freq, 0.16); });
    }
    if (e >= 2) {
      marimbaPattern(bar).forEach((n) => { if (n.step === step) this._voicePluck(t, n.freq, 0.1); });
    }
  };

  Engine.prototype._tick = function () {
    const LOOKAHEAD = 0.12;
    while (this.nextTime < this.ctx.currentTime + LOOKAHEAD) {
      this._scheduleStep(this.step, this.bar, this.nextTime);
      this.nextTime += SPB;
      this.step += 1;
      if (this.step >= STEPS) { this.step = 0; this.bar = (this.bar + 1) % BARS; }
    }
  };

  /*
   * Share one AudioContext with the rest of the game. iOS makes only ONE
   * context audible, so music, sound effects and animal calls must all
   * live on the same one or some of them are silent on a phone.
   */
  Engine.prototype.useContext = function (ctx) {
    if (!ctx) return false;
    this.ctx = ctx;
    this.master = ctx.createGain();
    this.master.gain.value = this.volume;
    this.master.connect(ctx.destination);
    this.noise = makeNoiseBuffer(ctx);
    return true;
  };

  /* Must be called from a user gesture — browsers block audio otherwise. */
  Engine.prototype.start = function () {
    if (this.playing) return;
    try {
      if (!this.ctx) {
        const Ctx = global.AudioContext || global.webkitAudioContext;
        if (!Ctx) return;
        this.ctx = new Ctx();
        this.master = this.ctx.createGain();
        this.master.gain.value = this.volume;
        this.master.connect(this.ctx.destination);
        this.noise = makeNoiseBuffer(this.ctx);
      }
      if (this.ctx.state === 'suspended') this.ctx.resume();
      this.step = 0; this.bar = 0;
      this.nextTime = this.ctx.currentTime + 0.06;
      this.playing = true;
      this.timer = setInterval(() => this._tick(), 25);
    } catch (err) { /* no audio on this device — the game plays on regardless */ }
  };

  Engine.prototype.stop = function () {
    this.playing = false;
    clearInterval(this.timer);
    this.timer = null;
  };

  Engine.prototype.setEnergy = function (level) { this.energy = level; };

  Engine.prototype.setVolume = function (v) {
    this.volume = v;
    if (this.master && this.ctx) {
      this.master.gain.setTargetAtTime(v, this.ctx.currentTime, 0.05);
    }
  };

  /*
   * Dip the groove so an animal call can be heard over it. Without this
   * the drums and riff sit right on top of the calls and bury them.
   */
  Engine.prototype.duck = function (seconds) {
    if (!this.playing || !this.master || !this.ctx) return;
    const t = this.ctx.currentTime;
    const hold = Math.min(1.2, Math.max(0.15, seconds || 0.4));
    this.master.gain.cancelScheduledValues(t);
    this.master.gain.setTargetAtTime(this.volume * 0.3, t, 0.02);
    this.master.gain.setTargetAtTime(this.volume, t + hold, 0.18);
  };

  /* A quick swell for a big cascade, then back down. */
  Engine.prototype.flourish = function () {
    if (!this.playing) return;
    const prev = this.energy;
    this.energy = 2;
    clearTimeout(this._fl);
    this._fl = setTimeout(() => { this.energy = prev; }, 3000);
  };

  const Music = {
    BPM, STEPS, BARS, SCALE, ROOTS,
    kickPattern, shakerPattern, clapPattern, bassPattern, riffPattern, marimbaPattern,
    Engine,
  };

  if (typeof module !== 'undefined' && module.exports) module.exports = Music;
  else global.NairobiMusic = Music;
})(typeof window !== 'undefined' ? window : globalThis);
