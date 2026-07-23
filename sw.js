// Gasmotion Service Worker v5.21
const CACHE_NAME = 'gasmotion-v521';
// Los DOS workers (sync y agenda/sales hub) van SIEMPRE a la red, sin caché:
// cachear respuestas de API muestra datos viejos y llena el almacenamiento.
const WORKER_DOMAINS = ['gasmotion-sync.geraldvlasof.workers.dev', 'gasmotion-worker.geraldvlasof.workers.dev'];
self.addEventListener('install', function(e) { self.skipWaiting(); });
self.addEventListener('activate', function(e) {
  e.waitUntil(
    caches.keys().then(function(keys) {
      return Promise.all(keys.filter(function(k){return k!==CACHE_NAME;}).map(function(k){return caches.delete(k);}));
    }).then(function(){ return self.clients.claim(); })
  );
});
self.addEventListener('fetch', function(e) {
  var url = e.request.url;
  var esWorker = false;
  for(var i=0;i<WORKER_DOMAINS.length;i++){ if(url.indexOf(WORKER_DOMAINS[i]) !== -1) esWorker = true; }
  if(esWorker) { e.respondWith(fetch(e.request, {cache:'no-store'})); return; }
  if(e.request.method === 'GET') {
    // Red primero (siempre fresco) pero con tope de 4s: si la conexion esta
    // lenta, se sirve la copia en cache al instante y la red actualiza detras.
    e.respondWith(
      new Promise(function(resolver){
        var resuelto = false;
        var temporizador = setTimeout(function(){
          caches.match(e.request).then(function(cacheada){
            if(cacheada && !resuelto){ resuelto = true; resolver(cacheada); }
          });
        }, 4000);
        fetch(e.request, {cache:'no-cache'})
        .then(function(res){
          if(res && res.status===200){ var c=res.clone(); caches.open(CACHE_NAME).then(function(ch){ch.put(e.request,c);}); }
          clearTimeout(temporizador);
          if(!resuelto){ resuelto = true; resolver(res); }
        })
        .catch(function(){
          clearTimeout(temporizador);
          if(!resuelto){ caches.match(e.request).then(function(cacheada){ resuelto = true; resolver(cacheada || Response.error()); }); }
        });
      })
    );
  }
});
