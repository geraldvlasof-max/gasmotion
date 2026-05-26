// Gasmotion Service Worker v3.0
// Solo cachea archivos estáticos — NUNCA cachea APIs

const CACHE_NAME = 'gasmotion-v30';
const STATIC_ASSETS = [
  '/',
  '/index.html'
];

// URLs que NUNCA deben cachearse (siempre van a la red)
const NO_CACHE_PATTERNS = [
  'gasmotion-sync.geraldvlasof.workers.dev',
  'script.google.com',
  'googleapis.com',
  'cloudflare',
  'action=',
  'workers.dev'
];

self.addEventListener('install', function(e) {
  e.waitUntil(
    caches.open(CACHE_NAME).then(function(cache) {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', function(e) {
  e.waitUntil(
    caches.keys().then(function(keys) {
      return Promise.all(
        keys.filter(function(k) { return k !== CACHE_NAME; })
            .map(function(k) { return caches.delete(k); })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', function(e) {
  var url = e.request.url;
  
  // NUNCA cachear llamadas a APIs
  for (var i = 0; i < NO_CACHE_PATTERNS.length; i++) {
    if (url.indexOf(NO_CACHE_PATTERNS[i]) !== -1) {
      // Ir directo a la red sin caché
      e.respondWith(fetch(e.request));
      return;
    }
  }
  
  // Para archivos estáticos: red primero, caché como fallback
  if (e.request.method === 'GET') {
    e.respondWith(
      fetch(e.request)
        .then(function(response) {
          // Cachear respuesta válida
          if (response && response.status === 200) {
            var clone = response.clone();
            caches.open(CACHE_NAME).then(function(cache) {
              cache.put(e.request, clone);
            });
          }
          return response;
        })
        .catch(function() {
          // Sin red: usar caché
          return caches.match(e.request);
        })
    );
  }
});
