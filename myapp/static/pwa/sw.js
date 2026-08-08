// Uzuklar Hukmdori — PWA service worker
// Ilova sifatida o'rnatish (Add to Home Screen / Install) imkonini beradi.
// Minimal keshlash: asosiy sahifa va ikonalarni saqlaydi, qolgan
// so'rovlarni har doim tarmoqdan oladi (sayt yangilanishlari darhol ko'rinadi).

const CACHE_NAME = "uh-shell-v1";
const APP_SHELL = [
  "/static/pwa/icon-192.png",
  "/static/pwa/icon-512.png",
  "/static/pwa/apple-touch-icon.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)).catch(() => {})
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;

  // Faqat o'zimizning ikonalarimiz uchun cache-first, qolgani uchun network-first
  if (APP_SHELL.some((p) => request.url.endsWith(p))) {
    event.respondWith(
      caches.match(request).then((cached) => cached || fetch(request))
    );
    return;
  }

  event.respondWith(
    fetch(request).catch(() => caches.match(request))
  );
});
