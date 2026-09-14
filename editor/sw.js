// sw.js — offline cache for the editor.
// Network-first with cache fallback: updates to index.html are picked up immediately,
// and the app shell still loads offline after the first visit.
const PREFIX = 'rich-editor-mvp:' + new URL('./', self.location.href).pathname + ':';
const CACHE = PREFIX + 'v1';
const ASSETS = ['./', './index.html', './sw.js'].map(path => new URL(path, self.location.href).href);

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    for (const key of await caches.keys()) if (key.startsWith(PREFIX) && key !== CACHE) await caches.delete(key);
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  url.search = '';
  if (event.request.method !== 'GET' || !ASSETS.includes(url.href)) return;
  event.respondWith((async () => {
    const cache = await caches.open(CACHE);
    try {
      const fresh = await fetch(event.request);
      if (fresh.ok) await cache.put(url.href, fresh.clone());
      return fresh;
    } catch {
      return (await cache.match(url.href)) || Response.error();
    }
  })());
});
