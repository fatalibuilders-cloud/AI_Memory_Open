/*
 * Service worker — the reason a shared link keeps working on the matatu.
 *
 * The whole game is one HTML file plus two icons, so there is no clever
 * caching to do: take the four files on first visit, then serve them from
 * the cache forever. After that first load the page costs nothing and opens
 * with the data off.
 *
 * VERSION is stamped by the deploy workflow. Changing it is what makes a new
 * release reach players: the browser byte-compares this file on every
 * navigation, a different VERSION means a new worker, and the new worker
 * throws the old cache away.
 */
const VERSION = 'dev';
const CACHE = 'nairobi-wild-' + VERSION;
const SHELL = ['./', './index.html', './manifest.webmanifest', './icon-192.png', './icon-512.png'];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE)
      // One missing file must not leave a player with no game at all, so
      // each is added on its own and a failure is survivable.
      .then((c) => Promise.all(SHELL.map((u) => c.add(u).catch(() => {}))))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== self.location.origin) return;

  // Cache first, then refresh in the background. The player never waits for
  // the network, and the next launch has whatever was published since.
  e.respondWith(
    caches.match(req).then((hit) => {
      const live = fetch(req)
        .then((res) => {
          if (res && res.ok) {
            const copy = res.clone();
            caches.open(CACHE).then((c) => c.put(req, copy));
          }
          return res;
        })
        .catch(() => hit);            // offline: the cache is the answer
      return hit || live;
    }),
  );
});
