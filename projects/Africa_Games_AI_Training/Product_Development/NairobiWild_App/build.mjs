/*
 * build.mjs — fold the seven module files into one self-contained page.
 *
 *   node build.mjs                  → nairobi-wild.html beside this file
 *   node build.mjs /path/out.html   → somewhere else
 *
 * The result is a single file with no external requests: open it from a
 * phone's Downloads folder, a WhatsApp attachment, or any static host and
 * it plays. A recorded sound pack is the one thing it cannot carry — that
 * still lives beside index.html as African_Wildlife_SFX/ (see its README).
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const out = resolve(process.argv[2] || resolve(here, 'nairobi-wild.html'));

let html = readFileSync(resolve(here, 'index.html'), 'utf8');
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

const kb = (Buffer.byteLength(html) / 1024).toFixed(0);
console.log(`${out}  ${kb} KB  (inlined: ${inlined.join(', ')})`);
