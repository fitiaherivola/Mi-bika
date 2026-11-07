/**
 * Service Worker Mi-bika — cache minimal pour mode hors-ligne (BNF2).
 */
const CACHE = 'mibika-v1';
const OFFLINE_URLS = ['/', '/static/css/base.css'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(OFFLINE_URLS))
  );
  self.skipWaiting();
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  event.respondWith(
    caches.match(event.request).then((cached) => {
      return cached || fetch(event.request).catch(() => caches.match('/'));
    })
  );
});
