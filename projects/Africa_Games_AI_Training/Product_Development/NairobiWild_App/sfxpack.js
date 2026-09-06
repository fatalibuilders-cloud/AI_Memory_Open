/*
 * Nairobi Wild — recorded sound pack loader
 *
 * The game ships with fully synthesised animal calls (sounds.js) so it works
 * with a ~150 KB install and no assets at all. This module lets REAL
 * recordings take over wherever they exist, animal by animal, without the
 * game code knowing or caring which it got.
 *
 * Expected layout on disk (drop the pack beside index.html):
 *
 *   African_Wildlife_SFX/
 *     01_LION/roar_01.ogg, roar_02.ogg, growl.ogg, snarl.ogg, distant_roar.ogg
 *     02_ELEPHANT/trumpet_01.ogg, trumpet_02.ogg, rumble.ogg, angry.ogg, herd.ogg
 *     03_HYENA/ … 20_RAIN_THUNDER/
 *     Android/optimized_OGG/      ← preferred: smaller, mobile-tuned
 *     LICENSE/credits.txt
 *
 * RULES THIS FOLLOWS
 * 1. NEVER block play. A call is synthesised immediately; a recording is
 *    used only once it is decoded and in memory.
 * 2. Fall back silently. An animal with no folder, or a file that fails to
 *    load, simply keeps its synthesised voice. Half a pack is fine.
 * 3. Load only what the current country needs, and only after the player
 *    has actually entered a stage — data costs money in this market.
 * 4. Never repeat the same variant twice running.
 *
 * WHERE THIS WORKS
 * In the packaged app (TWA/APK) and on any normal web host, files load
 * fine. Inside the claude.ai artifact preview they do NOT: that sandbox
 * blocks media fetches, so the preview always uses the synthesised voices.
 * That is expected, not a bug.
 */
(function (global) {
  'use strict';

  /*
   * Folder + variants per animal, matching the pack layout. `key` is the
   * animal key used by atlas.js; animals absent from this map (rhino,
   * camel, dodo, …) keep their synthesised voice.
   */
  const MANIFEST = {
    lion:      { dir: '01_LION',          variants: ['roar_01', 'roar_02', 'growl', 'snarl', 'distant_roar'] },
    elephant:  { dir: '02_ELEPHANT',      variants: ['trumpet_01', 'trumpet_02', 'rumble', 'angry', 'herd'] },
    hyena:     { dir: '03_HYENA',         variants: ['whoop_01', 'whoop_02', 'laugh', 'giggle'] },
    hippo:     { dir: '04_HIPPO',         variants: ['grunt_01', 'grunt_02', 'honk', 'splash'] },
    crocodile: { dir: '05_CROCODILE',     variants: ['hiss', 'growl', 'snap', 'bellow'] },
    leopard:   { dir: '06_LEOPARD',       variants: ['saw_01', 'saw_02', 'growl', 'snarl'] },
    cheetah:   { dir: '07_CHEETAH',       variants: ['chirp_01', 'chirp_02', 'purr', 'growl'] },
    gorilla:   { dir: '08_GORILLA',       variants: ['hoot_01', 'hoot_02', 'chest_beat', 'grunt'] },
    buffalo:   { dir: '09_BUFFALO',       variants: ['bellow_01', 'bellow_02', 'snort', 'herd'] },
    zebra:     { dir: '10_ZEBRA',         variants: ['bark_01', 'bark_02', 'whinny', 'snort'] },
    giraffe:   { dir: '11_GIRAFFE',       variants: ['hum', 'snort', 'bleat'] },
    monkey:    { dir: '12_MONKEY_BABOON', variants: ['chatter_01', 'chatter_02', 'screech', 'bark'] },
    warthog:   { dir: '13_WARTHOG',       variants: ['snort_01', 'snort_02', 'squeal', 'grunt'] },
    snake:     { dir: '14_SNAKE',         variants: ['hiss_01', 'hiss_02', 'rattle'] },
    eagle:     { dir: '15_EAGLE_BIRDS',   variants: ['eagle_01', 'eagle_02', 'screech', 'call'] },
    parrot:    { dir: '15_EAGLE_BIRDS',   variants: ['parrot_01', 'parrot_02', 'squawk'] },
  };

  /* Background beds, chosen by the region a stage sits in. */
  const AMBIENCE = {
    jungle:  { dir: '17_JUNGLE_AMBIENCE',  variants: ['jungle_loop'] },
    savanna: { dir: '18_SAVANNA_AMBIENCE', variants: ['savanna_loop'] },
    water:   { dir: '19_WATER',            variants: ['water_loop'] },
    rain:    { dir: '20_RAIN_THUNDER',     variants: ['rain_loop'] },
    insects: { dir: '16_INSECTS',          variants: ['insects_loop'] },
  };

  const REGION_AMBIENCE = {
    'East Africa': 'savanna',
    'Horn of Africa': 'savanna',
    'Southern Africa': 'savanna',
    'Central Africa': 'jungle',
    'West Africa': 'jungle',
    'North Africa': 'insects',
    'Indian Ocean': 'water',
  };

  const CONFIG = {
    /*
     * OFF by default, and deliberately so. Whether a pack shipped is a
     * BUILD-TIME fact, not something to discover by firing dozens of
     * speculative requests and reading the failures — the first cut of
     * this did exactly that and filled the console with 60+ errors while
     * costing a player real data. The packaged build turns it on with
     *     window.NAIROBI_WILD_SFX_PACK = true
     * (or NairobiSFX.configure({ enabled: true })), and then a single
     * request for pack.json says what is actually there.
     */
    enabled: false,
    // Set to '' to disable the pack entirely and always synthesise.
    basePath: 'African_Wildlife_SFX/',
    // Prefer the mobile-optimised folder, then the per-animal originals.
    dirPrefixes: ['Android/optimized_OGG/', ''],
    // Tried in order; ogg is smaller, m4a/mp3 covers older iOS.
    formats: ['ogg', 'm4a', 'mp3'],
    gain: 1.0,
    // Manifest listing what the pack actually contains. One request.
    indexFile: 'pack.json',
  };

  function configure(opts) {
    Object.keys(opts || {}).forEach(function (k) {
      if (k in CONFIG) CONFIG[k] = opts[k];
    });
  }

  /* Every URL worth trying for one variant, in priority order. */
  function candidateUrls(dir, variant) {
    if (!CONFIG.basePath) return [];
    const out = [];
    CONFIG.dirPrefixes.forEach(function (prefix) {
      CONFIG.formats.forEach(function (ext) {
        out.push(CONFIG.basePath + prefix + dir + '/' + variant + '.' + ext);
      });
    });
    return out;
  }

  function hasPackEntry(animalKey) {
    return !!MANIFEST[animalKey];
  }

  /* ---------------- the loader ---------------- */

  function SoundPack() {
    this.probed = null;     // Promise<boolean> — resolved once per session
    this.index = null;      // contents of pack.json, when present
    this.ctx = null;
    this.dest = null;
    this.buffers = {};      // 'lion/roar_01' -> AudioBuffer
    this.tried = {};        // urls already attempted, so we never refetch a 404
    this.loading = {};
    this.lastVariant = {};  // animal -> last variant played
    this.ambienceNode = null;
    this.stats = { loaded: 0, failed: 0 };
  }

  SoundPack.prototype.attach = function (ctx, destination) {
    if (!ctx) return false;
    this.ctx = ctx;
    this.master = ctx.createGain();
    this.master.gain.value = CONFIG.gain;
    this.master.connect(destination || ctx.destination);
    this.dest = destination || ctx.destination;
    return true;
  };

  /*
   * Ask once whether a pack is installed, by fetching its manifest. One
   * request, one answer, cached for the session. Without a manifest the
   * pack is treated as absent and nothing else is ever requested.
   */
  SoundPack.prototype.probe = function () {
    const self = this;
    if (this.probed) return this.probed;
    if (!CONFIG.enabled || !CONFIG.basePath) {
      this.probed = Promise.resolve(false);
      return this.probed;
    }
    this.probed = fetch(CONFIG.basePath + CONFIG.indexFile)
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (json) {
        if (!json) return false;
        self.index = json;
        if (json.dirPrefixes) CONFIG.dirPrefixes = json.dirPrefixes;
        if (json.formats) CONFIG.formats = json.formats;
        return true;
      })
      .catch(function () { return false; });
    return this.probed;
  };

  /* The variants the installed pack actually declares for an animal. */
  SoundPack.prototype._variants = function (animalKey) {
    if (this.index && this.index.animals && this.index.animals[animalKey]) {
      return this.index.animals[animalKey];
    }
    const entry = MANIFEST[animalKey];
    return entry ? entry.variants : [];
  };

  /* Fetch and decode one variant. Resolves null when the pack lacks it. */
  SoundPack.prototype._fetch = function (animalKey, variant) {
    const self = this;
    const id = animalKey + '/' + variant;
    if (this.buffers[id]) return Promise.resolve(this.buffers[id]);
    if (this.loading[id]) return this.loading[id];
    const entry = MANIFEST[animalKey];
    if (!entry || !this.ctx || !CONFIG.enabled) return Promise.resolve(null);

    const urls = candidateUrls(entry.dir, variant).filter(function (u) { return !self.tried[u]; });
    const attempt = function (i) {
      if (i >= urls.length) { self.stats.failed += 1; return Promise.resolve(null); }
      const url = urls[i];
      self.tried[url] = true;
      return fetch(url)
        .then(function (r) { return r.ok ? r.arrayBuffer() : Promise.reject(new Error('http ' + r.status)); })
        .then(function (buf) {
          return new Promise(function (resolve, reject) {
            // Callback form for older Safari, which lacks the promise form.
            const p = self.ctx.decodeAudioData(buf, resolve, reject);
            if (p && p.then) p.then(resolve, reject);
          });
        })
        .then(function (audio) {
          self.buffers[id] = audio;
          self.stats.loaded += 1;
          return audio;
        })
        .catch(function () { return attempt(i + 1); });
    };

    const job = attempt(0).then(function (b) { delete self.loading[id]; return b; });
    this.loading[id] = job;
    return job;
  };

  /*
   * Warm the six animals of a country in the background. Called when a
   * stage starts, never on the home screen — nobody should pay for data
   * they may not use.
   */
  SoundPack.prototype.preload = function (animalKeys) {
    const self = this;
    if (!this.ctx || !CONFIG.enabled) return Promise.resolve(0);
    return this.probe().then(function (installed) {
      if (!installed) return 0;
      const jobs = [];
      (animalKeys || []).forEach(function (k) {
        if (!MANIFEST[k]) return;
        // Two variants each is enough to avoid obvious repetition.
        self._variants(k).slice(0, 2).forEach(function (v) { jobs.push(self._fetch(k, v)); });
      });
      return Promise.all(jobs).then(function (r) { return r.filter(Boolean).length; });
    });
  };

  SoundPack.prototype.ready = function (animalKey) {
    if (!MANIFEST[animalKey]) return false;
    const self = this;
    return this._variants(animalKey).some(function (v) {
      return !!self.buffers[animalKey + '/' + v];
    });
  };

  /* Pick a decoded variant, avoiding an immediate repeat. */
  SoundPack.prototype._pick = function (animalKey) {
    if (!MANIFEST[animalKey]) return null;
    const self = this;
    const have = this._variants(animalKey).filter(function (v) {
      return !!self.buffers[animalKey + '/' + v];
    });
    if (have.length === 0) return null;
    const last = this.lastVariant[animalKey];
    const pool = have.length > 1 ? have.filter(function (v) { return v !== last; }) : have;
    const choice = pool[Math.floor(Math.random() * pool.length)];
    this.lastVariant[animalKey] = choice;
    return this.buffers[animalKey + '/' + choice];
  };

  /*
   * Play a recorded call. Returns FALSE when the pack cannot serve this
   * animal, which is the caller's signal to synthesise instead.
   */
  SoundPack.prototype.play = function (animalKey, opts) {
    if (!CONFIG.enabled || !this.ctx || !this.master) return false;
    const buf = this._pick(animalKey);
    // Nothing decoded for this animal: say so and let the caller
    // synthesise. Never start a fetch here — a miss during play would
    // cost data mid-move and, if no pack is installed, would fire on
    // every single match forever.
    if (!buf) return false;
    try {
      const src = this.ctx.createBufferSource();
      src.buffer = buf;
      // Pitch up slightly as a cascade builds, mirroring the synth voices.
      const combo = (opts && opts.combo) || 1;
      src.playbackRate.value = Math.min(1.45, 1 + (combo - 1) * 0.07) * (0.97 + Math.random() * 0.06);
      const g = this.ctx.createGain();
      g.gain.value = (opts && opts.gain) || 1;
      src.connect(g);
      g.connect(this.master);
      src.start();
      return true;
    } catch (e) {
      return false;
    }
  };

  /* A looping background bed for the region a stage sits in. */
  SoundPack.prototype.startAmbience = function (region, volume) {
    const self = this;
    if (!CONFIG.enabled || !this.ctx) return Promise.resolve(false);
    if (this.probed && this.index === null) return Promise.resolve(false);
    const key = REGION_AMBIENCE[region] || 'savanna';
    const entry = AMBIENCE[key];
    if (!entry) return Promise.resolve(false);
    const id = 'ambience/' + key;
    const urls = candidateUrls(entry.dir, entry.variants[0]);

    const load = this.buffers[id]
      ? Promise.resolve(this.buffers[id])
      : (function () {
        const attempt = function (i) {
          if (i >= urls.length) return Promise.resolve(null);
          return fetch(urls[i])
            .then(function (r) { return r.ok ? r.arrayBuffer() : Promise.reject(new Error('miss')); })
            .then(function (b) {
              return new Promise(function (res, rej) {
                const p = self.ctx.decodeAudioData(b, res, rej);
                if (p && p.then) p.then(res, rej);
              });
            })
            .then(function (a) { self.buffers[id] = a; return a; })
            .catch(function () { return attempt(i + 1); });
        };
        return attempt(0);
      }());

    return load.then(function (buf) {
      if (!buf) return false;
      self.stopAmbience();
      const src = self.ctx.createBufferSource();
      src.buffer = buf;
      src.loop = true;
      const g = self.ctx.createGain();
      g.gain.value = volume === undefined ? 0.18 : volume;
      src.connect(g);
      g.connect(self.dest || self.ctx.destination);
      src.start();
      self.ambienceNode = { src: src, gain: g };
      return true;
    });
  };

  SoundPack.prototype.stopAmbience = function () {
    if (!this.ambienceNode) return;
    try { this.ambienceNode.src.stop(); } catch (e) {}
    this.ambienceNode = null;
  };

  SoundPack.prototype.setVolume = function (v) {
    if (this.master && this.ctx) this.master.gain.setTargetAtTime(v, this.ctx.currentTime, 0.05);
  };

  /* Which animals the pack could cover, and which fall back to synthesis. */
  function coverage(animalKeys) {
    const recorded = [];
    const synthesised = [];
    (animalKeys || []).forEach(function (k) {
      (MANIFEST[k] ? recorded : synthesised).push(k);
    });
    return { recorded: recorded, synthesised: synthesised };
  }

  const SFX = {
    MANIFEST, AMBIENCE, REGION_AMBIENCE, CONFIG,
    configure, candidateUrls, hasPackEntry, coverage, SoundPack,
  };

  if (typeof module !== 'undefined' && module.exports) module.exports = SFX;
  else global.NairobiSFX = SFX;
})(typeof window !== 'undefined' ? window : globalThis);
