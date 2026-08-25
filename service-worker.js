// ========================================================
// SERVICE WORKER — MINHA AGENDA
// ========================================================

console.log("Service Worker carregado.");

// ========================================================
// INSTALAÇÃO
// ========================================================

self.addEventListener("install", function (event) {

    console.log("Service Worker: instalando...");

    // Ativa imediatamente a nova versão.
    self.skipWaiting();

});


// ========================================================
// ATIVAÇÃO
// ========================================================

self.addEventListener("activate", function (event) {

    console.log("Service Worker: ativado.");

    event.waitUntil(
        self.clients.claim()
    );

});


// ========================================================
// REQUISIÇÕES
// ========================================================

self.addEventListener("fetch", function (event) {

    // Deixa o navegador buscar normalmente.
    event.respondWith(
        fetch(event.request)
    );

});


// ========================================================
// MENSAGENS RECEBIDAS DA AGENDA
// ========================================================

self.addEventListener("message", function (event) {

    if (!event.data) {
        return;
    }

    if (event.data.tipo !== "NOTIFICAR") {
        return;
    }

    const dados = event.data.dados || {};

    const titulo =
        dados.titulo || "Minha Agenda";

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

            .then(function () {

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

            .catch(function (erro) {

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


// ========================================================
// CLIQUE NA NOTIFICAÇÃO
// ========================================================

self.addEventListener(
    "notificationclick",
    function (event) {

        event.notification.close();

        const url =
            event.notification.data &&
            event.notification.data.url
                ? event.notification.data.url
                : "/agenda_mobile.html";


        event.waitUntil(

            self.clients
                .matchAll({
                    type: "window",
                    includeUncontrolled: true
                })

                .then(function (clientes) {

                    for (const cliente of clientes) {

                        if ("focus" in cliente) {

                            cliente.focus();

                            if (
                                "navigate" in cliente
                            ) {

                                return cliente.navigate(
                                    url
                                );

                            }

                            return;

                        }

                    }

                    if (
                        self.clients.openWindow
                    ) {

                        return self.clients.openWindow(
                            url
                        );

                    }

                })

        );

    }

);