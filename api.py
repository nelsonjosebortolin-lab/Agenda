from flask import Flask, jsonify, request, send_from_directory
import agenda_core
import os


# ============================================================
# API DA AGENDA
# ============================================================

app = Flask(__name__)


# ============================================================
# LOCAL DOS ARQUIVOS DA AGENDA
# ============================================================

PASTA_AGENDA = os.path.dirname(
    os.path.abspath(__file__)
)


# ============================================================
# CABEÇALHOS PARA PERMITIR ACESSO DO CELULAR
# ============================================================

@app.after_request
def adicionar_cabecalhos(resposta):

    resposta.headers["Access-Control-Allow-Origin"] = "*"

    resposta.headers["Access-Control-Allow-Headers"] = (
        "Content-Type"
    )

    resposta.headers["Access-Control-Allow-Methods"] = (
        "GET, POST, PUT, DELETE, OPTIONS"
    )

    return resposta


# ============================================================
# PÁGINA PRINCIPAL DA AGENDA
# ============================================================

@app.route(
    "/",
    methods=["GET"]
)
def pagina_principal():

    return send_from_directory(
        PASTA_AGENDA,
        "agenda_mobile.html"
    )


# ============================================================
# MANIFESTO DO APLICATIVO
# ============================================================

@app.route(
    "/manifest.json",
    methods=["GET"]
)
def manifesto():

    return send_from_directory(
        PASTA_AGENDA,
        "manifest.json"
    )


# ============================================================
# ÍCONES DO APLICATIVO
# ============================================================

@app.route(
    "/icons/<nome_arquivo>",
    methods=["GET"]
)
def icones(nome_arquivo):

    pasta_icons = os.path.join(
        PASTA_AGENDA,
        "icons"
    )

    return send_from_directory(
        pasta_icons,
        nome_arquivo
    )


# ============================================================
# SERVICE WORKER
# ============================================================

@app.route(
    "/service-worker.js",
    methods=["GET"]
)
def service_worker():

    resposta = send_from_directory(
        PASTA_AGENDA,
        "service-worker.js"
    )

    resposta.headers["Content-Type"] = (
        "application/javascript"
    )

    return resposta


# ============================================================
# WEB PUSH — BASE PARA NOTIFICAÇÕES NO CELULAR
# ============================================================

# Nesta primeira etapa, o servidor apenas recebe e guarda
# a inscrição (subscription) fornecida pelo navegador.
#
# O envio real das notificações será acrescentado depois,
# quando configurarmos as chaves VAPID e o mecanismo de
# verificação dos lembretes.


@app.route(
    "/api/push/inscricao",
    methods=["POST"]
)
def registrar_inscricao_push():

    dados = request.get_json(
        silent=True
    )

    if not dados:

        return jsonify({
            "erro": "Nenhum dado recebido"
        }), 400

    endpoint = dados.get(
        "endpoint"
    )

    if not endpoint:

        return jsonify({
            "erro": "A inscrição não possui endpoint"
        }), 400

    try:

        # Guardamos a inscrição em arquivo JSON por enquanto.
        # Isso evita alterar o banco agenda.db nesta primeira etapa.
        caminho = os.path.join(
            PASTA_AGENDA,
            "push_subscription.json"
        )

        with open(
            caminho,
            "w",
            encoding="utf-8"
        ) as arquivo:

            import json

            json.dump(
                dados,
                arquivo,
                ensure_ascii=False,
                indent=4
            )

    except Exception as erro:

        return jsonify({
            "erro": str(erro)
        }), 500

    return jsonify({

        "ok": True,

        "mensagem":
            "Inscrição de notificações registrada."

    })


# ============================================================
# TESTE DA API
# ============================================================

# ============================================================

@app.route(
    "/api/status",
    methods=["GET"]
)
def status():

    return jsonify({
        "ok": True,
        "mensagem": "Agenda funcionando"
    })


# ============================================================
# LISTAR EVENTOS
# ============================================================

@app.route(
    "/api/eventos",
    methods=["GET"]
)
def listar_eventos():

    filtro = request.args.get(
        "filtro",
        ""
    )

    eventos = agenda_core.listar_eventos_ordenados(
        filtro
    )

    resultado = []

    for evento in eventos:

        resultado.append({

            "id":
                evento["id"],

            "tipo":
                evento["tipo"],

            "nome":
                evento["nome"],

            "data":
                evento["data"],

            "horario":
                evento["horario"],

            "avisar_horas":
                evento["avisar_horas"],

            "detalhe":
                evento["detalhe"],

            "recorrente":
                evento["recorrente"],

            "aviso_enviado":
                evento["aviso_enviado"],

            "ultimo_aviso_ano":
                evento["ultimo_aviso_ano"],

            "avisar_dias":
                evento["avisar_dias"],

            "horario_aviso":
                evento["horario_aviso"],

            "aviso_no_dia":
                evento["aviso_no_dia"],

            "proximo_aviso":
                evento["proximo_aviso"]

        })

    return jsonify(resultado)


# ============================================================
# BUSCAR UM EVENTO
# ============================================================

@app.route(
    "/api/eventos/<int:id_evento>",
    methods=["GET"]
)
def buscar_evento(id_evento):

    evento = agenda_core.obter_evento(
        id_evento
    )

    if evento is None:

        return jsonify({
            "erro": "Evento não encontrado"
        }), 404

    (
        id_evento,
        tipo,
        nome,
        data,
        horario,
        avisar_horas,
        detalhe,
        recorrente,
        aviso_enviado,
        ultimo_aviso_ano,
        avisar_dias,
        horario_aviso,
        aviso_no_dia
    ) = evento

    return jsonify({

        "id":
            id_evento,

        "tipo":
            tipo,

        "nome":
            nome,

        "data":
            data,

        "horario":
            horario,

        "avisar_horas":
            avisar_horas,

        "detalhe":
            detalhe,

        "recorrente":
            recorrente,

        "aviso_enviado":
            aviso_enviado,

        "ultimo_aviso_ano":
            ultimo_aviso_ano,

        "avisar_dias":
            avisar_dias,

        "horario_aviso":
            horario_aviso,

        "aviso_no_dia":
            aviso_no_dia

    })


# ============================================================
# CRIAR EVENTO
# ============================================================

@app.route(
    "/api/eventos",
    methods=["POST"]
)
def criar_evento():

    dados = request.get_json(
        silent=True
    )

    if not dados:

        return jsonify({
            "erro": "Nenhum dado recebido"
        }), 400

    tipo = dados.get(
        "tipo",
        "Compromisso"
    )

    nome = dados.get(
        "nome",
        ""
    ).strip()

    data = dados.get(
        "data",
        ""
    )

    horario = dados.get(
        "horario"
    )

    avisar_horas = dados.get(
        "avisar_horas",
        0
    )

    detalhe = dados.get(
        "detalhe",
        ""
    )

    recorrente = dados.get(
        "recorrente",
        0
    )

    avisar_dias = dados.get(
        "avisar_dias",
        0
    )

    horario_aviso = dados.get(
        "horario_aviso"
    )

    aviso_no_dia = dados.get(
        "aviso_no_dia",
        1
    )

    if not nome:

        return jsonify({
            "erro": "O nome do evento é obrigatório"
        }), 400

    try:

        id_evento = agenda_core.criar_evento(

            tipo=tipo,

            nome=nome,

            data=data,

            horario=horario,

            avisar_horas=int(
                avisar_horas
            ),

            detalhe=detalhe,

            recorrente=int(
                recorrente
            ),

            avisar_dias=int(
                avisar_dias
            ),

            horario_aviso=horario_aviso,

            aviso_no_dia=int(
                aviso_no_dia
            )

        )

    except Exception as erro:

        return jsonify({
            "erro": str(erro)
        }), 400

    return jsonify({

        "ok":
            True,

        "id":
            id_evento

    }), 201


# ============================================================
# ALTERAR EVENTO
# ============================================================

@app.route(
    "/api/eventos/<int:id_evento>",
    methods=["PUT"]
)
def atualizar_evento(id_evento):

    dados = request.get_json(
        silent=True
    )

    if not dados:

        return jsonify({
            "erro": "Nenhum dado recebido"
        }), 400

    tipo = dados.get(
        "tipo",
        "Compromisso"
    )

    nome = dados.get(
        "nome",
        ""
    ).strip()

    data = dados.get(
        "data",
        ""
    )

    horario = dados.get(
        "horario"
    )

    avisar_horas = dados.get(
        "avisar_horas",
        0
    )

    detalhe = dados.get(
        "detalhe",
        ""
    )

    recorrente = dados.get(
        "recorrente",
        0
    )

    avisar_dias = dados.get(
        "avisar_dias",
        0
    )

    horario_aviso = dados.get(
        "horario_aviso"
    )

    aviso_no_dia = dados.get(
        "aviso_no_dia",
        1
    )

    if not nome:

        return jsonify({
            "erro": "O nome do evento é obrigatório"
        }), 400

    try:

        alterado = agenda_core.atualizar_evento(

            id_evento=id_evento,

            tipo=tipo,

            nome=nome,

            data=data,

            horario=horario,

            avisar_horas=int(
                avisar_horas
            ),

            detalhe=detalhe,

            recorrente=int(
                recorrente
            ),

            avisar_dias=int(
                avisar_dias
            ),

            horario_aviso=horario_aviso,

            aviso_no_dia=int(
                aviso_no_dia
            )

        )

    except Exception as erro:

        return jsonify({
            "erro": str(erro)
        }), 400

    if not alterado:

        return jsonify({
            "erro": "Evento não encontrado"
        }), 404

    return jsonify({

        "ok":
            True,

        "mensagem":
            "Evento atualizado"

    })


# ============================================================
# EXCLUIR EVENTO
# ============================================================

@app.route(
    "/api/eventos/<int:id_evento>",
    methods=["DELETE"]
)
def excluir_evento(id_evento):

    excluido = agenda_core.excluir_evento(
        id_evento
    )

    if not excluido:

        return jsonify({
            "erro": "Evento não encontrado"
        }), 404

    return jsonify({

        "ok":
            True,

        "mensagem":
            "Evento excluído"

    })


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":

    agenda_core.criar_banco()

    print()

    print("=" * 55)

    print(
        "API DA MINHA AGENDA"
    )

    print("=" * 55)

    print()

    print(
        "Servidor iniciado."
    )

    print(
        "Computador: http://127.0.0.1:5000"
    )

    print(
        "Rede local: http://192.168.0.178:5000"
    )

    print()

    print(
        "Não feche esta janela enquanto estiver testando."
    )

    print()

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=False

    )