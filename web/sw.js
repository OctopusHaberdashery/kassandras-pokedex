// Keeps the app itself on the device so it opens without internet.
// The page is always fetched fresh when online (so updates arrive right away), with the saved copy as a fallback.
// Price data is saved by the app itself, so it isn't cached here.
const CACHE = "pokedex-app-v1";
const SHELL = ["./", "./index.html", "./manifest.webmanifest", "./icons/icon-192.png", "./icons/icon-512.png",
  "./icons/apple-touch-icon.png", "./icons/maskable-512.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const req = e.request, url = new URL(req.url);
  if (req.method !== "GET" || url.origin !== location.origin || url.pathname.includes("/data/")) return;
  e.respondWith((async () => {
    const cache = await caches.open(CACHE);
    const key = req.mode === "navigate" ? "./index.html" : req;
    const network = fetch(req).then(r => { if (r.ok) cache.put(key, r.clone()); return r; });
    const saved = await cache.match(key);
    if (!saved) return network;
    // online: use the fresh copy if it arrives within 3 seconds, otherwise the saved one
    const timeout = new Promise(res => setTimeout(() => res(saved), 3000));
    try { return await Promise.race([network, timeout]); } catch (err) { return saved; }
  })());
});
