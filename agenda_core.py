import sqlite3
from datetime import datetime, timedelta


# ============================================================
# BANCO DE DADOS DA AGENDA
# ============================================================

BANCO = "agenda.db"


# ============================================================
# CONEXÃO
# ============================================================

def conectar():
    return sqlite3.connect(BANCO)


# ============================================================
# ESTRUTURA DO BANCO
# ============================================================

def adicionar_coluna_se_nao_existir(
    cursor,
    tabela,
    coluna,
    definicao
):
    cursor.execute(
        f"PRAGMA table_info({tabela})"
    )

    colunas = [
        linha[1]
        for linha in cursor.fetchall()
    ]

    if coluna not in colunas:
        cursor.execute(
            f"ALTER TABLE {tabela} "
            f"ADD COLUMN {coluna} {definicao}"
        )


def criar_banco():

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            nome TEXT NOT NULL,
            data TEXT NOT NULL,
            horario TEXT,
            avisar_horas INTEGER DEFAULT 0,
            detalhe TEXT,
            recorrente INTEGER DEFAULT 0,
            aviso_enviado INTEGER DEFAULT 0,
            ultimo_aviso_ano TEXT,
            avisar_dias INTEGER DEFAULT 0,
            horario_aviso TEXT,
            aviso_no_dia INTEGER DEFAULT 1
        )
    """)

    adicionar_coluna_se_nao_existir(
        cursor,
        "eventos",
        "recorrente",
        "INTEGER DEFAULT 0"
    )

    adicionar_coluna_se_nao_existir(
        cursor,
        "eventos",
        "aviso_enviado",
        "INTEGER DEFAULT 0"
    )

    adicionar_coluna_se_nao_existir(
        cursor,
        "eventos",
        "ultimo_aviso_ano",
        "TEXT"
    )

    adicionar_coluna_se_nao_existir(
        cursor,
        "eventos",
        "avisar_dias",
        "INTEGER DEFAULT 0"
    )

    adicionar_coluna_se_nao_existir(
        cursor,
        "eventos",
        "horario_aviso",
        "TEXT"
    )

    adicionar_coluna_se_nao_existir(
        cursor,
        "eventos",
        "aviso_no_dia",
        "INTEGER DEFAULT 1"
    )

    conexao.commit()
    conexao.close()


# ============================================================
# VALIDAÇÕES
# ============================================================

def validar_data_compromisso(data):

    try:
        datetime.strptime(
            data,
            "%d/%m/%Y"
        )
        return True

    except ValueError:
        return False


def validar_data_aniversario(data):

    try:
        datetime.strptime(
            data,
            "%d/%m"
        )
        return True

    except ValueError:
        return False


def validar_horario(horario):

    try:
        datetime.strptime(
            horario,
            "%H:%M"
        )
        return True

    except ValueError:
        return False


# ============================================================
# CRIAR EVENTO
# ============================================================

def criar_evento(
    tipo,
    nome,
    data,
    horario=None,
    avisar_horas=0,
    detalhe="",
    recorrente=0,
    avisar_dias=0,
    horario_aviso=None,
    aviso_no_dia=1
):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        INSERT INTO eventos (
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
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tipo,
        nome,
        data,
        horario,
        avisar_horas,
        detalhe,
        recorrente,
        0,
        None,
        avisar_dias,
        horario_aviso,
        aviso_no_dia
    ))

    id_evento = cursor.lastrowid

    conexao.commit()
    conexao.close()

    return id_evento


# ============================================================
# ATUALIZAR EVENTO
# ============================================================

def atualizar_evento(
    id_evento,
    tipo,
    nome,
    data,
    horario=None,
    avisar_horas=0,
    detalhe="",
    recorrente=0,
    avisar_dias=0,
    horario_aviso=None,
    aviso_no_dia=1
):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        UPDATE eventos
        SET
            tipo = ?,
            nome = ?,
            data = ?,
            horario = ?,
            avisar_horas = ?,
            detalhe = ?,
            recorrente = ?,
            aviso_enviado = 0,
            ultimo_aviso_ano = NULL,
            avisar_dias = ?,
            horario_aviso = ?,
            aviso_no_dia = ?
        WHERE id = ?
    """, (
        tipo,
        nome,
        data,
        horario,
        avisar_horas,
        detalhe,
        recorrente,
        avisar_dias,
        horario_aviso,
        aviso_no_dia,
        id_evento
    ))

    alterado = cursor.rowcount > 0

    conexao.commit()
    conexao.close()

    return alterado


# ============================================================
# EXCLUIR EVENTO
# ============================================================

def excluir_evento(id_evento):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute(
        "DELETE FROM eventos WHERE id = ?",
        (id_evento,)
    )

    excluido = cursor.rowcount > 0

    conexao.commit()
    conexao.close()

    return excluido


# ============================================================
# BUSCAR UM EVENTO
# ============================================================

def obter_evento(id_evento):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            id,
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
        FROM eventos
        WHERE id = ?
    """, (
        id_evento,
    ))

    evento = cursor.fetchone()

    conexao.close()

    return evento


# ============================================================
# LISTAR EVENTOS
# ============================================================

def listar_eventos(filtro=""):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            id,
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
        FROM eventos
    """)

    eventos = cursor.fetchall()

    conexao.close()

    if not filtro:
        return eventos

    filtro = filtro.lower()

    resultado = []

    for evento in eventos:

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

        texto = (
            f"{nome} "
            f"{tipo} "
            f"{data} "
            f"{detalhe or ''}"
        ).lower()

        if filtro in texto:
            resultado.append(evento)

    return resultado


# ============================================================
# PRÓXIMA OCORRÊNCIA
# ============================================================

def obter_proxima_ocorrencia(
    tipo,
    data,
    horario
):

    agora = datetime.now()

    if tipo == "Compromisso":

        try:

            return datetime.strptime(
                f"{data} {horario}",
                "%d/%m/%Y %H:%M"
            )

        except (
            ValueError,
            TypeError
        ):

            return datetime.max

    try:

        dia, mes = data.split("/")

        hora = 0
        minuto = 0

        if horario and horario != "-":

            hora, minuto = map(
                int,
                horario.split(":")
            )

        ano = agora.year

        ocorrencia = datetime(
            ano,
            int(mes),
            int(dia),
            hora,
            minuto
        )

        if ocorrencia < agora:

            ocorrencia = datetime(
                ano + 1,
                int(mes),
                int(dia),
                hora,
                minuto
            )

        return ocorrencia

    except (
        ValueError,
        TypeError
    ):

        return datetime.max


# ============================================================
# PRÓXIMO AVISO
# ============================================================

def obter_proximo_aviso(
    tipo,
    data,
    horario,
    aviso_horas,
    aviso_dias,
    horario_aviso
):

    agora = datetime.now()

    if tipo == "Compromisso":

        try:

            evento = datetime.strptime(
                f"{data} {horario}",
                "%d/%m/%Y %H:%M"
            )

            aviso = (
                evento
                - timedelta(
                    hours=aviso_horas
                )
            )

            if aviso < agora:

                if evento >= agora:

                    return "Já devido"

                return "Já passou"

            return aviso.strftime(
                "%d/%m/%Y %H:%M"
            )

        except (
            ValueError,
            TypeError
        ):

            return "-"

    try:

        dia, mes = data.split("/")

        hora, minuto = map(
            int,
            (
                horario_aviso or "08:00"
            ).split(":")
        )

        ano = agora.year

        aniversario = datetime(
            ano,
            int(mes),
            int(dia),
            hora,
            minuto
        )

        aviso_antecipado = (
            aniversario
            - timedelta(
                days=aviso_dias
            )
        )

        if aviso_dias > 0:

            if aviso_antecipado >= agora:

                return aviso_antecipado.strftime(
                    "%d/%m/%Y %H:%M"
                )

        if aniversario >= agora:

            return aniversario.strftime(
                "%d/%m/%Y %H:%M"
            )

        aniversario_proximo = datetime(
            ano + 1,
            int(mes),
            int(dia),
            hora,
            minuto
        )

        aviso_proximo = (
            aniversario_proximo
            - timedelta(
                days=aviso_dias
            )
        )

        if aviso_dias > 0:

            return aviso_proximo.strftime(
                "%d/%m/%Y %H:%M"
            )

        return aniversario_proximo.strftime(
            "%d/%m/%Y %H:%M"
        )

    except (
        ValueError,
        TypeError
    ):

        return "-"


# ============================================================
# EVENTOS ORDENADOS
# ============================================================

def listar_eventos_ordenados(
    filtro=""
):

    eventos = listar_eventos(
        filtro
    )

    resultado = []

    for evento in eventos:

        (
            id_evento,
            tipo,
            nome,
            data,
            horario,
            aviso_horas,
            detalhe,
            recorrente,
            aviso_enviado,
            ultimo_aviso_ano,
            aviso_dias,
            horario_aviso,
            aviso_no_dia
        ) = evento

        horario_para_ordem = (
            horario
            if tipo == "Compromisso"
            else horario_aviso
        )

        proxima_data = (
            obter_proxima_ocorrencia(
                tipo,
                data,
                horario_para_ordem
            )
        )

        proximo_aviso = (
            obter_proximo_aviso(
                tipo,
                data,
                horario,
                aviso_horas,
                aviso_dias,
                horario_aviso
            )
        )

        resultado.append({
            "id": id_evento,
            "tipo": tipo,
            "nome": nome,
            "data": data,
            "horario": horario,
            "avisar_horas": aviso_horas,
            "detalhe": detalhe,
            "recorrente": recorrente,
            "aviso_enviado": aviso_enviado,
            "ultimo_aviso_ano": ultimo_aviso_ano,
            "avisar_dias": aviso_dias,
            "horario_aviso": horario_aviso,
            "aviso_no_dia": aviso_no_dia,
            "proxima_data": proxima_data,
            "proximo_aviso": proximo_aviso
        })

    resultado.sort(
        key=lambda evento:
        evento["proxima_data"]
    )

    return resultado


# ============================================================
# INICIALIZAÇÃO
# ============================================================

criar_banco()