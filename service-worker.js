const CACHE_NAME = "agenda-cache-v4";

const ARQUIVOS = [
    "/",
    "/index.html",
    "/agenda_mobile.html",
    "/manifest.json",
    "/icons/icon-192.png",
    "/icons/icon-512.png"
];

self.addEventListener("install", (event) => {
    console.log("Service Worker: instalando...");

    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                return cache.addAll(ARQUIVOS);
            })
            .then(() => {
                return self.skipWaiting();
            })
    );
});

self.addEventListener("activate", (event) => {
    console.log("Service Worker: ativando...");

    event.waitUntil(
        caches.keys()
            .then((nomesCaches) => {
                return Promise.all(
                    nomesCaches
                        .filter((nome) => nome !== CACHE_NAME)
                        .map((nome) => caches.delete(nome))
                );
            })
            .then(() => {
                return self.clients.claim();
            })
    );
});

self.addEventListener("fetch", (event) => {
    const request = event.request;

    if (request.method !== "GET") {
        return;
    }

    event.respondWith(
        caches.match(request)
            .then((respostaCache) => {
                if (respostaCache) {
                    return respostaCache;
                }

                return fetch(request)
                    .then((respostaRede) => {

                        if (
                            !respostaRede ||
                            respostaRede.status !== 200 ||
                            respostaRede.type === "opaque"
                        ) {
                            return respostaRede;
                        }

                        const respostaParaCache = respostaRede.clone();

                        caches.open(CACHE_NAME)
                            .then((cache) => {
                                cache.put(request, respostaParaCache);
                            });

                        return respostaRede;
                    })
                    .catch(() => {
                        return caches.match("/agenda_mobile.html");
                    });
            })
    );
});


/*
========================================================
NOTIFICAÇÕES
========================================================
*/

self.addEventListener("notificationclick", (event) => {
    event.notification.close();

    event.waitUntil(
        clients.matchAll({
            type: "window",
            includeUncontrolled: true
        })
        .then((listaClientes) => {

            for (const cliente of listaClientes) {

                if ("focus" in cliente) {
                    return cliente.focus();
                }
            }

            if (clients.openWindow) {
                return clients.openWindow("/agenda_mobile.html");
            }
        })
    );
});


/*
========================================================
MENSAGENS RECEBIDAS DA AGENDA
========================================================
*/

self.addEventListener("message", (event) => {

    if (!event.data) {
        return;
    }

    if (event.data.tipo !== "NOTIFICAR") {
        return;
    }

    const dados =
        event.data.dados || {};

    const titulo =
        dados.titulo || "Agenda";

    const opcoes = {

        body:
            dados.mensagem ||
            "Você tem um compromisso.",

        icon:
            "/icons/icon-192.png",

        badge:
            "/icons/icon-192.png",

        tag:
            dados.tag ||
            "agenda-compromisso",

        renotify: true,

        requireInteraction: true,

        data: {
            url:
                dados.url ||
                "/agenda_mobile.html"
        }

    };


    event.waitUntil(

        self.registration.showNotification(
            titulo,
            opcoes
        )

    );

});
