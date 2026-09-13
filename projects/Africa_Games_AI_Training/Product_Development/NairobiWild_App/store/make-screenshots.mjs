import { createRequire } from 'node:module';
import { mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const require_ = createRequire(import.meta.url);
// Playwright is only a rendering device here: these assets are SVG and HTML,
// and a browser is the one thing guaranteed to draw them the same way twice.
const { chromium } = require_(process.env.PLAYWRIGHT_PATH || 'playwright');
const HERE = dirname(fileURLToPath(import.meta.url));
const CHROME = process.env.CHROMIUM_PATH || undefined;
const APP = process.argv[2] || resolve(HERE, '../nairobi-wild.html');
const OUT = resolve(HERE, 'screenshots');
mkdirSync(OUT, { recursive: true });

// Play wants phone shots between 320 and 3840 px with an aspect ratio no
// wider than 2:1. 360x640 at 3x lands on exactly 1080x1920 — a real phone
// resolution, safely inside every rule.
const browser = await chromium.launch(CHROME ? { executablePath: CHROME } : {});
const page = await browser.newPage({ viewport: { width: 360, height: 640 }, deviceScaleFactor: 3 });
const errors = [];
page.on('pageerror', e => errors.push(String(e.message)));

const shot = (n, name) => page.screenshot({ path: `${OUT}/${n}-${name}.png` });

await page.goto('file://' + APP);
await page.waitForTimeout(600);
await shot(1, 'home');

// A board mid-cascade says more than an untouched one.
await page.click('#btnPlay'); await page.waitForTimeout(300);
await shot(3, 'countries');
await page.click('#stalls .stall:not([disabled])'); await page.waitForTimeout(300);
await shot(4, 'cities');
await page.click('#cityList .stall:not([disabled])'); await page.waitForTimeout(300);
await page.click('#stGo'); await page.waitForTimeout(800);

for (let k = 0; k < 4; k += 1) {
  const pair = await page.evaluate(() => {
    const C = 8, R = 8;
    const b = [...document.querySelectorAll('#board .tile')].map(t => t.dataset.c);
    const lines = (g) => {
      for (let r = 0; r < R; r += 1) for (let c = 0; c < C; c += 1) {
        const v = g[r * C + c]; if (v === undefined) continue;
        if (c <= C - 3 && g[r * C + c + 1] === v && g[r * C + c + 2] === v) return true;
        if (r <= R - 3 && g[(r + 1) * C + c] === v && g[(r + 2) * C + c] === v) return true;
      }
      return false;
    };
    for (let i = 0; i < R * C; i += 1) for (const j of [i + 1, i + C]) {
      if (j >= R * C) continue;
      if (j === i + 1 && Math.floor(i / C) !== Math.floor(j / C)) continue;
      const g = b.slice(); const t = g[i]; g[i] = g[j]; g[j] = t;
      if (lines(g)) return [i, j];
    }
    return null;
  });
  if (!pair) break;
  await page.click(`#board .tile[data-i="${pair[0]}"]`); await page.waitForTimeout(60);
  await page.click(`#board .tile[data-i="${pair[1]}"]`); await page.waitForTimeout(1100);
}
await shot(2, 'board');

// Back out to the menu for the rest.
for (const b of ['#btnGameBack', '#btnCityBack', '#btnMapBack']) {
  const el = await page.$(b + ':visible');
  if (el) { await el.click(); await page.waitForTimeout(300); }
}
await page.click('#btnVoices'); await page.waitForTimeout(400);
await shot(5, 'animal-calls');
await page.click('#voicesClose'); await page.waitForTimeout(200);
await page.click('#btnDuel'); await page.waitForTimeout(400);
await shot(6, 'duels');

console.log(errors.length ? 'ERRORS: ' + errors.join(' | ') : 'no JS errors');
await browser.close();
