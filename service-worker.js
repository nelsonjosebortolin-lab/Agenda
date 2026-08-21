const CACHE_NAME = "agenda-cache-v2";

const ARQUIVOS = [
    "/",
    "/manifest.json",
    "/icons/icon-192.png",
    "/icons/icon-512.png"
];


self.addEventListener("install", function(event) {

    event.waitUntil(

        caches.open(CACHE_NAME)
            .then(function(cache) {

                return cache.addAll(ARQUIVOS);

            })

    );

    self.skipWaiting();

});


self.addEventListener("activate", function(event) {

    event.waitUntil(

        caches.keys()
            .then(function(nomes) {

                return Promise.all(

                    nomes.map(function(nome) {

                        if (nome !== CACHE_NAME) {

                            return caches.delete(nome);

                        }

                    })

                );

            })

    );

    self.clients.claim();

});


self.addEventListener("fetch", function(event) {

    event.respondWith(

        fetch(event.request)
            .catch(function() {

                return caches.match(event.request);

            })

    );

});