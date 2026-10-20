// Gasmotion Service Worker v5.95 (retiro): el panel se mudó al worker.
// Se instala al instante, borra la caché del panel viejo, se da de baja y
// recarga las pestañas abiertas para que lleguen a la página de redirección.
const CACHE_NAME = 'gasmotion-v595-retiro';
self.addEventListener('install', function () { self.skipWaiting(); });
self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys()
      .then(function (keys) { return Promise.all(keys.map(function (k) { return caches.delete(k); })); })
      .then(function () { return self.registration.unregister(); })
      .then(function () { return self.clients.matchAll({ type: 'window' }); })
      .then(function (clientes) { clientes.forEach(function (c) { try { c.navigate(c.url); } catch (e) {} }); })
  );
});
self.addEventListener('message', function (e) {
  if (e.data && e.data.type === 'SKIP_WAITING') self.skipWaiting();
});
