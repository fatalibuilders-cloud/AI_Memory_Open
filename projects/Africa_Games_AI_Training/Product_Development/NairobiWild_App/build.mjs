/*
 * build.mjs — fold the seven module files into one self-contained page.
 *
 *   node build.mjs                  → nairobi-wild.html beside this file
 *   node build.mjs /path/out.html   → somewhere else
 *   node build.mjs out.html --web   → keep the manifest and icon tags
 *
 * The default result is a single file with no external requests at all: open
 * it from a phone's Downloads folder, a WhatsApp attachment, or the APK's own
 * assets and it plays, asking for nothing. The web-only block in index.html —
 * the manifest, the icons, the Apple full-screen tags — is stripped, because
 * those files sit on the web host and a standalone copy would only sit there
 * failing to fetch them.
 *
 * `--web` keeps them, for the GitHub Pages build where they do exist and are
 * what turns the page into something installable from a shared link.
 *
 * A recorded sound pack is the one thing this cannot carry — that still lives
 * beside index.html as African_Wildlife_SFX/ (see its README).
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const web = args.includes('--web');
const out = resolve(args.find((a) => !a.startsWith('--')) || resolve(here, 'nairobi-wild.html'));

let html = readFileSync(resolve(here, 'index.html'), 'utf8');

if (!web) {
  const before = html.length;
  html = html.replace(/<!-- web-only:start[\s\S]*?<!-- web-only:end -->\n?/g, '');
  if (html.length === before) throw new Error('the web-only block was not found to strip');
}
const tag = /<script src="([^"]+)"><\/script>\n?/g;
const inlined = [];

html = html.replace(tag, (_, src) => {
  const code = readFileSync(resolve(here, src), 'utf8');
  inlined.push(src);
  // </script> inside a string literal would close the tag early.
  return `<script>\n/* ${src} */\n${code.replace(/<\/script>/g, '<\\/script>')}\n</script>\n`;
});

if (tag.test(html)) throw new Error('a <script src> survived inlining');
writeFileSync(out, html);

// A standalone build that still points at a manifest is the bug this guards.
if (!web && /manifest\.webmanifest|icon-192\.png/.test(html)) {
  throw new Error('standalone build still references a web-only file');
}

const kb = (Buffer.byteLength(html) / 1024).toFixed(0);
console.log(`${out}  ${kb} KB  ${web ? '[web]' : '[standalone]'}  (inlined: ${inlined.join(', ')})`);
