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
const RES = resolve(HERE, '../android/app/src/main/res');
const STORE = HERE;

// Android's five density buckets: mdpi is 1x, and every launcher icon is
// 48dp while the adaptive foreground is 108dp.
const DPI = { mdpi: 1, hdpi: 1.5, xhdpi: 2, xxhdpi: 3, xxxhdpi: 4 };

const jobs = [];
for (const [bucket, k] of Object.entries(DPI)) {
  mkdirSync(`${RES}/mipmap-${bucket}`, { recursive: true });
  jobs.push({ art: 'icon', w: Math.round(48 * k), h: Math.round(48 * k), alpha: true,
              out: `${RES}/mipmap-${bucket}/ic_launcher.png` });
  jobs.push({ art: 'fore', w: Math.round(108 * k), h: Math.round(108 * k), alpha: true,
              out: `${RES}/mipmap-${bucket}/ic_launcher_foreground.png` });
}
mkdirSync(STORE, { recursive: true });
jobs.push({ art: 'store', w: 512, h: 512, alpha: false, out: `${STORE}/play-icon-512.png` });
jobs.push({ art: 'feature', w: 1024, h: 500, alpha: false, out: `${STORE}/play-feature-1024x500.png` });

// The web build's home-screen icons. Same art as the store icon, which is
// full-bleed with the tile well inside the centre — so it survives being
// masked into a circle or a squircle, and can be declared "maskable".
const WEB = resolve(HERE, '../web');
mkdirSync(WEB, { recursive: true });
jobs.push({ art: 'store', w: 192, h: 192, alpha: false, out: `${WEB}/icon-192.png` });
jobs.push({ art: 'store', w: 512, h: 512, alpha: false, out: `${WEB}/icon-512.png` });

const browser = await chromium.launch(CHROME ? { executablePath: CHROME } : {});
for (const j of jobs) {
  const page = await browser.newPage({ viewport: { width: j.w, height: j.h }, deviceScaleFactor: 1 });
  await page.goto(`file://${HERE}/art.html?art=${j.art}`);
  await page.waitForTimeout(120);
  await page.screenshot({ path: j.out, omitBackground: j.alpha });
  await page.close();
  console.log(`${j.w}x${j.h}  ${j.out}`);
}
await browser.close();
