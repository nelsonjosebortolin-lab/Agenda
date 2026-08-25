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
    console.log("Service Worker: instalando v4...");

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
    console.log("Service Worker: ativando v4...");

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

    /*
    Para a página da Agenda, tentar primeiro a rede.
    Isso evita que o celular fique preso a uma
    versão antiga do HTML.
    */

    if (
        request.mode === "navigate" ||
        request.url.includes("/agenda_mobile.html")
    ) {

        event.respondWith(

            fetch(request)
                .then((respostaRede) => {

                    if (
                        respostaRede &&
                        respostaRede.status === 200
                    ) {

                        const copia =
                            respostaRede.clone();

                        caches.open(CACHE_NAME)
                            .then((cache) => {
                                cache.put(
                                    request,
                                    copia
                                );
                            });

                        return respostaRede;
                    }

                    return caches.match(request);
                })
                .catch(() => {

                    return caches.match(request)
                        .then((respostaCache) => {

                            if (respostaCache) {
                                return respostaCache;
                            }

                            return caches.match(
                                "/agenda_mobile.html"
                            );
                        });
                })
        );

        return;
    }


    /*
    Demais arquivos:
    primeiro tenta o cache e depois a rede.
    */

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

                        const respostaParaCache =
                            respostaRede.clone();

                        caches.open(CACHE_NAME)
                            .then((cache) => {

                                cache.put(
                                    request,
                                    respostaParaCache
                                );

                            });

                        return respostaRede;

                    })
                    .catch(() => {

                        return caches.match(
                            "/agenda_mobile.html"
                        );

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
                return clients.openWindow(
                    "/agenda_mobile.html"
                );
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

        self.registration
            .showNotification(
                titulo,
                opcoes
            )

            .then(() => {

                console.log(
                    "Notificação mostrada com sucesso."
                );

                if (
                    event.ports &&
                    event.ports[0]
                ) {

                    event.ports[0].postMessage({
                        ok: true
                    });

                }

            })

            .catch((erro) => {

                console.error(
                    "Erro no showNotification:",
                    erro
                );

                if (
                    event.ports &&
                    event.ports[0]
                ) {

                    event.ports[0].postMessage({
                        ok: false,
                        erro:
                            erro.message ||
                            String(erro)
                    });

                }

            })

    );

});