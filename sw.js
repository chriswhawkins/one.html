// sw.js — opt-in service worker for the Kitchen Sink demo.
// Strategy: network-first with cache fallback, so edits to index.html always show up
// while the page still loads offline once it has been visited.
const PREFIX = 'kitchen-sink-sw:' + new URL('./', self.location.href).pathname + ':';
const CACHE = PREFIX + 'v1';
const ASSETS = ['./', './index.html', './sw.js'].map(path => new URL(path, self.location.href).href);

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting()));
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

self.addEventListener('message', (event) => {
  if (event.data?.type === 'ping') {
    const reply = { type: 'pong', receivedAt: Date.now(), roundTripStart: event.data.t, cache: CACHE };
    if (event.ports?.[0]) event.ports[0].postMessage(reply); else event.source?.postMessage(reply);
  }
});
