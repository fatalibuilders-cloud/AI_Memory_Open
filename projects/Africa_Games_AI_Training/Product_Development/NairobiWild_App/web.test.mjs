/*
 * Does the shared link actually behave like an app?
 *
 * Serves the built site over http://localhost (a secure context, so service
 * workers are live) and checks the three things a friend on a phone will
 * notice: it installs, it survives the network going away, and it keeps
 * their progress.
 */
import { createRequire } from 'node:module';
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const require_ = createRequire(import.meta.url);
const { chromium } = require_(process.env.PLAYWRIGHT_PATH || 'playwright');
const HERE = dirname(fileURLToPath(import.meta.url));
const SITE = resolve(HERE, '_site');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript',
                '.png': 'image/png', '.webmanifest': 'application/manifest+json' };

const missing = [];
const server = createServer(async (req, res) => {
  const path = req.url.split('?')[0];
  const file = join(SITE, path === '/' ? 'index.html' : path);
  try {
    const body = await readFile(file);
    res.writeHead(200, { 'content-type': TYPES[extname(file)] || 'application/octet-stream' });
    res.end(body);
  } catch {
    missing.push(path);
    res.writeHead(404).end('not found');
  }
});
await new Promise((ok) => server.listen(0, '127.0.0.1', ok));
const URL_ = `http://127.0.0.1:${server.address().port}/`;

const browser = await chromium.launch(
  process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});
const ctx = await browser.newContext({ viewport: { width: 412, height: 880 } });
const page = await ctx.newPage();
const errors = [];
page.on('pageerror', (e) => errors.push(e.message));
page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });

const checks = [];
const check = (name, ok, detail) => { checks.push({ name, ok, detail }); };

await page.goto(URL_);
await page.waitForTimeout(500);

// 1. The manifest is real and says what the home-screen icon should be.
const manifest = await page.evaluate(async () => {
  const link = document.querySelector('link[rel="manifest"]');
  if (!link) return null;
  const r = await fetch(link.href);
  return r.ok ? r.json() : null;
});
check('manifest loads', !!manifest);
check('manifest is standalone', manifest && manifest.display === 'standalone', manifest && manifest.display);
check('manifest has a maskable icon',
      !!(manifest && manifest.icons || []).length
      && manifest.icons.every((i) => String(i.purpose || '').includes('maskable')));

// 2. The worker takes control, which is what makes the second visit free.
const controlled = await page.evaluate(() =>
  navigator.serviceWorker.ready.then((reg) => !!reg.active).catch(() => false));
check('service worker active', controlled);

const cached = await page.evaluate(async () => {
  const names = await caches.keys();
  if (!names.length) return [];
  const c = await caches.open(names[0]);
  return (await c.keys()).map((r) => new URL(r.url).pathname).sort();
});
check('shell cached', cached.length >= 4, cached.join(' '));

// 3. Earn a star, so there is progress worth keeping.
await page.click('#btnPlay'); await page.waitForTimeout(250);
await page.click('#stalls .stall:not([disabled])'); await page.waitForTimeout(250);
await page.click('#cityList .stall:not([disabled])'); await page.waitForTimeout(250);
await page.click('#stGo'); await page.waitForTimeout(700);
const play = async () => page.evaluate(() => {
  const C = 8, R = 8;
  const b = [...document.querySelectorAll('#board .tile')].map((t) => t.dataset.c);
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
for (let k = 0; k < 2; k += 1) {
  const p = await play(); if (!p) break;
  await page.click(`#board .tile[data-i="${p[0]}"]`); await page.waitForTimeout(60);
  await page.click(`#board .tile[data-i="${p[1]}"]`); await page.waitForTimeout(1100);
}
const score = await page.evaluate(() =>
  Number(document.getElementById('scoreN').textContent.replace(/,/g, '')));
check('a move scores', score > 0, String(score));

// 4. Cut the network entirely and open it again — the matatu test.
await ctx.setOffline(true);
const offline = await ctx.newPage();
const offErrors = [];
offline.on('pageerror', (e) => offErrors.push(e.message));
await offline.goto(URL_, { waitUntil: 'load' });
await offline.waitForTimeout(600);
const title = await offline.title();
const homeVisible = await offline.isVisible('#btnPlay');
check('loads with the network off', title === 'Nairobi Wild' && homeVisible,
      `title=${JSON.stringify(title)} play=${homeVisible}`);
check('no errors while offline', offErrors.length === 0, offErrors.join(' | '));

// 5. Progress survives, because the save is in localStorage, not the cache.
const saved = await offline.evaluate(() => !!localStorage.getItem('nairobiWild.v1'));
check('save file survives', saved);

// A browser asks for /favicon.ico whether or not you declare one. Anything
// missing here is a file a real phone would also fail to fetch.
check('nothing 404s', missing.length === 0, missing.join(' '));

await browser.close();
server.close();

let bad = 0;
for (const c of checks) {
  if (!c.ok) bad += 1;
  console.log(`${c.ok ? 'ok  ' : 'FAIL'}  ${c.name}${c.detail ? '  — ' + c.detail : ''}`);
}
if (errors.length) console.log('page errors: ' + errors.join(' | '));
console.log(bad ? `${bad} check(s) failed` : `all ${checks.length} checks passed`);
process.exit(bad || errors.length ? 1 : 0);
