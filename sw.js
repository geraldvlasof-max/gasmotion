// Gasmotion Service Worker v3.0
const CACHE_NAME = 'gasmotion-v3';
const ASSETS = [
  '/gasmotion/',
  '/gasmotion/index.html',
  '/gasmotion/manifest.json',
  '/gasmotion/icon-192.png',
  '/gasmotion/icon-512.png'
];

self.addEventListener('install', function(e) {
  e.waitUntil(caches.open(CACHE_NAME).then(function(c){ return c.addAll(ASSETS); }));
  self.skipWaiting();
});

self.addEventListener('activate', function(e) {
  e.waitUntil(caches.keys().then(function(keys){
    return Promise.all(keys.filter(function(k){return k!==CACHE_NAME;}).map(function(k){return caches.delete(k);}));
  }));
  self.clients.claim();
});

self.addEventListener('fetch', function(e) {
  if(e.request.method!=='GET') return;
  if(e.request.url.includes('googleapis.com')||e.request.url.includes('google.com')) return;
  e.respondWith(
    caches.match(e.request).then(function(cached){
      if(cached) return cached;
      return fetch(e.request).then(function(r){
        if(r&&r.status===200){
          var clone=r.clone();
          caches.open(CACHE_NAME).then(function(c){c.put(e.request,clone);});
        }
        return r;
      }).catch(function(){ return caches.match('/gasmotion/'); });
    })
  );
});
