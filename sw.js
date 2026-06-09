// Gasmotion Service Worker v4.1 — Network First, No API Cache
const CACHE_NAME = 'gasmotion-v41';
const WORKER_DOMAIN = 'gasmotion-sync.geraldvlasof.workers.dev';
self.addEventListener('install', function(e) {
  self.skipWaiting(); // Activar inmediatamente sin esperar
});
self.addEventListener('activate', function(e) {
  e.waitUntil(
    caches.keys().then(function(keys) {
      return Promise.all(
        keys.filter(function(k) { return k !== CACHE_NAME; })
            .map(function(k) { return caches.delete(k); })
      );
    }).then(function() {
      return self.clients.claim(); // Tomar control inmediato de todos los tabs
    })
  );
});
self.addEventListener('fetch', function(e) {
  var url = e.request.url;
  
  // NUNCA cachear el Worker de Cloudflare
  if(url.indexOf(WORKER_DOMAIN) !== -1) {
    e.respondWith(fetch(e.request, {cache: 'no-store'}));
    return;
  }
  
  // Para todo lo demás: red primero, caché como fallback offline
  if(e.request.method === 'GET') {
    e.respondWith(
      fetch(e.request, {cache: 'no-cache'})
      .then(function(res) {
        if(res && res.status === 200) {
          var clone = res.clone();
          caches.open(CACHE_NAME).then(function(c){ c.put(e.request, clone); });
        }
        return res;
      })
      .catch(function() {
        return caches.match(e.request);
      })
    );
  }
});
