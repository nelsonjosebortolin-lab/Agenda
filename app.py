import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
import threading
import queue
import agenda_core

from winotify import Notification, audio
import pystray
from PIL import Image, ImageDraw


# ============================================================
# CONFIGURAÇÕES
# ============================================================

BANCO = "agenda.db"

evento_editando = None

tray_icon = None

# Fila de comunicação entre o ícone e o Tkinter
fila_tray = queue.Queue()


# ============================================================
# BANCO DE DADOS
# ============================================================

def conectar():
    return sqlite3.connect(BANCO)


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
# FUNÇÕES AUXILIARES
# ============================================================

def somente_numeros(texto):

    return "".join(
        caractere
        for caractere in texto
        if caractere.isdigit()
    )


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
# FORMATAÇÃO DE DATA
# ============================================================

def formatar_data_compromisso(event=None):

    texto = somente_numeros(
        entrada_data.get()
    )

    texto = texto[:8]

    if len(texto) <= 2:

        resultado = texto

    elif len(texto) <= 4:

        resultado = (
            texto[:2]
            + "/"
            + texto[2:]
        )

    else:

        resultado = (
            texto[:2]
            + "/"
            + texto[2:4]
            + "/"
            + texto[4:]
        )

    entrada_data.delete(
        0,
        tk.END
    )

    entrada_data.insert(
        0,
        resultado
    )


def formatar_data_aniversario(event=None):

    texto = somente_numeros(
        entrada_data.get()
    )

    texto = texto[:4]

    if len(texto) <= 2:

        resultado = texto

    else:

        resultado = (
            texto[:2]
            + "/"
            + texto[2:]
        )

    entrada_data.delete(
        0,
        tk.END
    )

    entrada_data.insert(
        0,
        resultado
    )


# ============================================================
# FORMATAÇÃO DE HORÁRIO
# ============================================================

def formatar_horario(event=None):

    texto = somente_numeros(
        entrada_horario.get()
    )

    texto = texto[:4]

    if len(texto) <= 2:

        resultado = texto

    else:

        resultado = (
            texto[:2]
            + ":"
            + texto[2:]
        )

    entrada_horario.delete(
        0,
        tk.END
    )

    entrada_horario.insert(
        0,
        resultado
    )


def formatar_horario_aviso(event=None):

    texto = somente_numeros(
        entrada_horario_aviso.get()
    )

    texto = texto[:4]

    if len(texto) <= 2:

        resultado = texto

    else:

        resultado = (
            texto[:2]
            + ":"
            + texto[2:]
        )

    entrada_horario_aviso.delete(
        0,
        tk.END
    )

    entrada_horario_aviso.insert(
        0,
        resultado
    )


# ============================================================
# PLACEHOLDERS
# ============================================================

def foco_data(event=None):

    if entrada_data.get() in (
        "DD/MM/AAAA",
        "DD/MM"
    ):

        entrada_data.delete(
            0,
            tk.END
        )


def sair_data(event=None):

    if not entrada_data.get().strip():

        if tipo_evento.get() == "Compromisso":

            entrada_data.insert(
                0,
                "DD/MM/AAAA"
            )

        else:

            entrada_data.insert(
                0,
                "DD/MM"
            )


def foco_horario(event=None):

    if entrada_horario.get() == "HH:MM":

        entrada_horario.delete(
            0,
            tk.END
        )


def sair_horario(event=None):

    if not entrada_horario.get().strip():

        entrada_horario.insert(
            0,
            "HH:MM"
        )


# ============================================================
# ALTERAR TIPO
# ============================================================

def alterar_tipo(event=None):

    tipo = tipo_evento.get()

    entrada_data.unbind(
        "<KeyRelease>"
    )

    entrada_horario.unbind(
        "<KeyRelease>"
    )

    entrada_horario_aviso.unbind(
        "<KeyRelease>"
    )

    if tipo == "Compromisso":

        entrada_data.config(
            state="normal"
        )

        entrada_data.delete(
            0,
            tk.END
        )

        entrada_data.insert(
            0,
            "DD/MM/AAAA"
        )

        entrada_data.bind(
            "<KeyRelease>",
            formatar_data_compromisso
        )

        entrada_horario.config(
            state="normal"
        )

        entrada_horario.delete(
            0,
            tk.END
        )

        entrada_horario.insert(
            0,
            "HH:MM"
        )

        entrada_horario.bind(
            "<KeyRelease>",
            formatar_horario
        )

        entrada_aviso_horas.config(
            state="normal"
        )

        entrada_aviso_horas.delete(
            0,
            tk.END
        )

        entrada_aviso_horas.insert(
            0,
            "24"
        )

        entrada_aviso_dias.config(
            state="disabled"
        )

        entrada_aviso_dias.delete(
            0,
            tk.END
        )

        entrada_aviso_dias.insert(
            0,
            "-"
        )

        entrada_horario_aviso.config(
            state="disabled"
        )

        entrada_horario_aviso.delete(
            0,
            tk.END
        )

        entrada_horario_aviso.insert(
            0,
            "-"
        )

        texto_data.config(
            text="Data:"
        )

        texto_horario.config(
            text="Horário:"
        )

    else:

        entrada_data.config(
            state="normal"
        )

        entrada_data.delete(
            0,
            tk.END
        )

        entrada_data.insert(
            0,
            "DD/MM"
        )

        entrada_data.bind(
            "<KeyRelease>",
            formatar_data_aniversario
        )

        entrada_horario.config(
            state="disabled"
        )

        entrada_horario.delete(
            0,
            tk.END
        )

        entrada_horario.insert(
            0,
            "-"
        )

        entrada_aviso_horas.config(
            state="disabled"
        )

        entrada_aviso_horas.delete(
            0,
            tk.END
        )

        entrada_aviso_horas.insert(
            0,
            "-"
        )

        entrada_aviso_dias.config(
            state="normal"
        )

        entrada_aviso_dias.delete(
            0,
            tk.END
        )

        entrada_aviso_dias.insert(
            0,
            "3"
        )

        entrada_horario_aviso.config(
            state="normal"
        )

        entrada_horario_aviso.delete(
            0,
            tk.END
        )

        entrada_horario_aviso.insert(
            0,
            "08:00"
        )

        entrada_horario_aviso.bind(
            "<KeyRelease>",
            formatar_horario_aviso
        )

        texto_data.config(
            text="Data do aniversário:"
        )

        texto_horario.config(
            text="Horário do compromisso:"
        )


# ============================================================
# LIMPAR CAMPOS
# ============================================================

def limpar_campos():

    global evento_editando

    evento_editando = None

    entrada_nome.delete(
        0,
        tk.END
    )

    entrada_data.delete(
        0,
        tk.END
    )

    entrada_horario.delete(
        0,
        tk.END
    )

    entrada_aviso_horas.delete(
        0,
        tk.END
    )

    entrada_aviso_dias.delete(
        0,
        tk.END
    )

    entrada_horario_aviso.delete(
        0,
        tk.END
    )

    entrada_detalhe.delete(
        "1.0",
        tk.END
    )

    tipo_evento.set(
        "Compromisso"
    )

    alterar_tipo()

    botao_cadastrar.config(
        text="CADASTRAR"
    )

    botao_cancelar.config(
        state="disabled"
    )


# ============================================================
# SALVAR EVENTO
# ============================================================

def salvar_evento():

    global evento_editando

    tipo = tipo_evento.get()

    nome = entrada_nome.get().strip()

    data = entrada_data.get().strip()

    detalhe = entrada_detalhe.get(
        "1.0",
        tk.END
    ).strip()

    if not nome:

        messagebox.showwarning(
            "Atenção",
            "Informe o compromisso ou o nome da pessoa."
        )

        return

    if tipo == "Compromisso":

        horario = entrada_horario.get().strip()

        aviso_horas = (
            entrada_aviso_horas
            .get()
            .strip()
        )

        if not validar_data_compromisso(
            data
        ):

            messagebox.showwarning(
                "Data inválida",
                "Informe a data no formato DD/MM/AAAA."
            )

            return

        if not validar_horario(
            horario
        ):

            messagebox.showwarning(
                "Horário inválido",
                "Informe o horário no formato HH:MM."
            )

            return

        if not aviso_horas.isdigit():

            messagebox.showwarning(
                "Atenção",
                "Informe quantas horas antes deseja ser avisado."
            )

            return

        aviso_horas = int(
            aviso_horas
        )

        if (
            aviso_horas < 0
            or aviso_horas > 999
        ):

            messagebox.showwarning(
                "Atenção",
                "O número de horas deve estar entre 0 e 999."
            )

            return

        avisar_dias = 0
        horario_aviso = None
        recorrente = 0
        aviso_no_dia = 0

    else:

        horario = None
        aviso_horas = 0

        avisar_dias = (
            entrada_aviso_dias
            .get()
            .strip()
        )

        horario_aviso = (
            entrada_horario_aviso
            .get()
            .strip()
        )

        if not validar_data_aniversario(
            data
        ):

            messagebox.showwarning(
                "Data inválida",
                "Informe o aniversário no formato DD/MM."
            )

            return

        if not avisar_dias.isdigit():

            messagebox.showwarning(
                "Atenção",
                "Informe quantos dias antes deseja ser avisado."
            )

            return

        avisar_dias = int(
            avisar_dias
        )

        if (
            avisar_dias < 0
            or avisar_dias > 365
        ):

            messagebox.showwarning(
                "Atenção",
                "O número de dias deve estar entre 0 e 365."
            )

            return

        if not validar_horario(
            horario_aviso
        ):

            messagebox.showwarning(
                "Horário inválido",
                "Informe o horário do aviso no formato HH:MM."
            )

            return

        recorrente = 1
        aviso_no_dia = 1

    conexao = conectar()
    cursor = conexao.cursor()

    if evento_editando is None:

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
            aviso_horas,
            detalhe,
            recorrente,
            0,
            None,
            avisar_dias,
            horario_aviso,
            aviso_no_dia
        ))

        mensagem = (
            "Evento cadastrado com sucesso!"
        )

    else:

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
            aviso_horas,
            detalhe,
            recorrente,
            avisar_dias,
            horario_aviso,
            aviso_no_dia,
            evento_editando
        ))

        mensagem = (
            "Evento atualizado com sucesso!"
        )

    conexao.commit()
    conexao.close()

    messagebox.showinfo(
        "Sucesso",
        mensagem
    )

    limpar_campos()

    carregar_eventos()


# ============================================================
# PESQUISA
# ============================================================

def filtrar_eventos(event=None):

    carregar_eventos(
        filtro=entrada_pesquisa
        .get()
        .strip()
    )


def limpar_pesquisa():

    entrada_pesquisa.delete(
        0,
        tk.END
    )

    carregar_eventos()


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
# CARREGAR EVENTOS
# ============================================================

def carregar_eventos(
    filtro=""
):

    for item in tabela.get_children():

        tabela.delete(
            item
        )

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
            avisar_dias,
            horario_aviso
        FROM eventos
    """)

    eventos = cursor.fetchall()

    conexao.close()

    eventos_ordenados = []

    filtro_lower = filtro.lower()

    for evento in eventos:

        (
            id_evento,
            tipo,
            nome,
            data,
            horario,
            aviso_horas,
            detalhe,
            aviso_dias,
            horario_aviso
        ) = evento

        if filtro_lower:

            texto_busca = (
                f"{nome} "
                f"{tipo} "
                f"{data} "
                f"{detalhe or ''}"
            ).lower()

            if (
                filtro_lower
                not in texto_busca
            ):

                continue

        proxima_data = (
            obter_proxima_ocorrencia(
                tipo,
                data,
                horario
                if tipo == "Compromisso"
                else horario_aviso
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

        if tipo == "Aniversário":

            horario_exibido = (
                horario_aviso or "-"
            )

            regra = (
                f"{aviso_dias} "
                f"dias antes + no dia"
            )

        else:

            horario_exibido = (
                horario or "-"
            )

            regra = (
                f"{aviso_horas} h antes"
            )

        eventos_ordenados.append(
            (
                proxima_data,
                (
                    id_evento,
                    tipo,
                    nome,
                    data,
                    horario_exibido,
                    regra,
                    proximo_aviso
                )
            )
        )

    eventos_ordenados.sort(
        key=lambda x: x[0]
    )

    for _, valores in eventos_ordenados:

        tabela.insert(
            "",
            tk.END,
            values=valores
        )


# ============================================================
# EDITAR
# ============================================================

def editar_evento():

    global evento_editando

    selecionado = tabela.selection()

    if not selecionado:

        messagebox.showwarning(
            "Atenção",
            "Selecione um evento para editar."
        )

        return

    item = tabela.item(
        selecionado[0]
    )

    id_evento = item["values"][0]

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
            avisar_dias,
            horario_aviso
        FROM eventos
        WHERE id = ?
    """, (
        id_evento,
    ))

    evento = cursor.fetchone()

    conexao.close()

    if evento is None:
        return

    (
        id_evento,
        tipo,
        nome,
        data,
        horario,
        aviso_horas,
        detalhe,
        aviso_dias,
        horario_aviso
    ) = evento

    evento_editando = id_evento

    tipo_evento.set(
        tipo
    )

    alterar_tipo()

    entrada_nome.delete(
        0,
        tk.END
    )

    entrada_nome.insert(
        0,
        nome
    )

    entrada_data.delete(
        0,
        tk.END
    )

    entrada_data.insert(
        0,
        data
    )

    if tipo == "Compromisso":

        entrada_horario.delete(
            0,
            tk.END
        )

        entrada_horario.insert(
            0,
            horario or ""
        )

        entrada_aviso_horas.delete(
            0,
            tk.END
        )

        entrada_aviso_horas.insert(
            0,
            str(aviso_horas)
        )

    else:

        entrada_aviso_dias.delete(
            0,
            tk.END
        )

        entrada_aviso_dias.insert(
            0,
            str(aviso_dias)
        )

        entrada_horario_aviso.delete(
            0,
            tk.END
        )

        entrada_horario_aviso.insert(
            0,
            horario_aviso or "08:00"
        )

    entrada_detalhe.delete(
        "1.0",
        tk.END
    )

    entrada_detalhe.insert(
        "1.0",
        detalhe or ""
    )

    botao_cadastrar.config(
        text="SALVAR ALTERAÇÕES"
    )

    botao_cancelar.config(
        state="normal"
    )

    mostrar_janela()


# ============================================================
# EXCLUIR
# ============================================================

def excluir_evento():

    selecionado = tabela.selection()

    if not selecionado:

        messagebox.showwarning(
            "Atenção",
            "Selecione um evento para excluir."
        )

        return

    item = tabela.item(
        selecionado[0]
    )

    id_evento = item["values"][0]
    nome = item["values"][2]

    confirmar = messagebox.askyesno(
        "Confirmar exclusão",
        f"Deseja excluir:\n\n{nome}?"
    )

    if not confirmar:
        return

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute(
        "DELETE FROM eventos WHERE id = ?",
        (id_evento,)
    )

    conexao.commit()
    conexao.close()

    limpar_campos()

    carregar_eventos(
        filtro=entrada_pesquisa
        .get()
        .strip()
    )


# ============================================================
# VERIFICAR LEMBRETES
# ============================================================

def verificar_lembretes():

    agora = datetime.now()

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

        if tipo == "Compromisso":

            try:

                data_evento = datetime.strptime(
                    f"{data} {horario}",
                    "%d/%m/%Y %H:%M"
                )

            except (
                ValueError,
                TypeError
            ):

                continue

            momento_aviso = (
                data_evento
                - timedelta(
                    hours=avisar_horas
                )
            )

            if (
                agora >= momento_aviso
                and aviso_enviado == 0
            ):

                mostrar_aviso(
                    "Lembrete de compromisso",
                    nome,
                    data_evento,
                    detalhe
                )

                cursor.execute("""
                    UPDATE eventos
                    SET aviso_enviado = 1
                    WHERE id = ?
                """, (
                    id_evento,
                ))

        elif tipo == "Aniversário":

            try:

                dia, mes = data.split("/")

                horario_do_aviso = (
                    horario_aviso or "08:00"
                )

                hora, minuto = map(
                    int,
                    horario_do_aviso.split(":")
                )

                ano_atual = agora.year

                aniversario = datetime(
                    ano_atual,
                    int(mes),
                    int(dia),
                    hora,
                    minuto
                )

            except (
                ValueError,
                TypeError
            ):

                continue

            data_aniversario = (
                aniversario.date()
            )

            data_atual = (
                agora.date()
            )

            if data_atual == data_aniversario:

                chave_no_dia = (
                    f"{ano_atual}-DIA"
                )

                if (
                    aviso_no_dia == 1
                    and agora >= aniversario
                    and ultimo_aviso_ano
                    != chave_no_dia
                ):

                    mostrar_aviso_aniversario(
                        "Aniversário hoje",
                        nome,
                        aniversario,
                        detalhe,
                        0
                    )

                    cursor.execute("""
                        UPDATE eventos
                        SET ultimo_aviso_ano = ?
                        WHERE id = ?
                    """, (
                        chave_no_dia,
                        id_evento
                    ))

                continue

            if data_atual < data_aniversario:

                momento_antecipado = (
                    aniversario
                    - timedelta(
                        days=avisar_dias
                    )
                )

                chave_antecipada = (
                    f"{ano_atual}-ANTECIPADO"
                )

                if (
                    avisar_dias > 0
                    and agora >= momento_antecipado
                    and agora < aniversario
                    and ultimo_aviso_ano
                    != chave_antecipada
                ):

                    mostrar_aviso_aniversario(
                        "Aniversário chegando",
                        nome,
                        aniversario,
                        detalhe,
                        avisar_dias
                    )

                    cursor.execute("""
                        UPDATE eventos
                        SET ultimo_aviso_ano = ?
                        WHERE id = ?
                    """, (
                        chave_antecipada,
                        id_evento
                    ))

    conexao.commit()
    conexao.close()

    janela.after(
        10000,
        verificar_lembretes
    )


# ============================================================
# NOTIFICAÇÃO DE COMPROMISSO
# ============================================================

def mostrar_aviso(
    titulo,
    nome,
    data_evento,
    detalhe
):

    mensagem = (
        f"{nome}\n"
        f"Data: "
        f"{data_evento.strftime('%d/%m/%Y')}\n"
        f"Horário: "
        f"{data_evento.strftime('%H:%M')}"
    )

    if detalhe:

        mensagem += (
            f"\n\nDetalhe:\n"
            f"{detalhe}"
        )

    try:

        notificacao = Notification(
            app_id="Minha Agenda",
            title=titulo,
            msg=mensagem,
            duration="long"
        )

        notificacao.set_audio(
            audio.Default,
            loop=False
        )

        notificacao.show()

    except Exception:

        messagebox.showinfo(
            titulo,
            mensagem
        )


# ============================================================
# NOTIFICAÇÃO DE ANIVERSÁRIO
# ============================================================

def mostrar_aviso_aniversario(
    titulo,
    nome,
    aniversario,
    detalhe,
    dias
):

    if dias > 1:

        mensagem = (
            f"Aniversário de {nome}\n"
            f"Faltam {dias} dias.\n"
            f"Data: "
            f"{aniversario.strftime('%d/%m')}"
        )

    elif dias == 1:

        mensagem = (
            f"Aniversário de {nome}\n"
            f"É amanhã!\n"
            f"Data: "
            f"{aniversario.strftime('%d/%m')}"
        )

    else:

        mensagem = (
            f"Hoje é aniversário de {nome}!\n"
            f"Data: "
            f"{aniversario.strftime('%d/%m')}"
        )

    if detalhe:

        mensagem += (
            f"\n\nDetalhe:\n"
            f"{detalhe}"
        )

    try:

        notificacao = Notification(
            app_id="Minha Agenda",
            title=titulo,
            msg=mensagem,
            duration="long"
        )

        notificacao.set_audio(
            audio.Default,
            loop=False
        )

        notificacao.show()

    except Exception:

        messagebox.showinfo(
            titulo,
            mensagem
        )


# ============================================================
# ÍCONE DA ÁREA DE NOTIFICAÇÃO
# ============================================================

def criar_icone_tray():

    imagem = Image.new(
        "RGB",
        (64, 64),
        "white"
    )

    desenho = ImageDraw.Draw(
        imagem
    )

    desenho.rounded_rectangle(
        (4, 4, 60, 60),
        radius=10,
        fill="blue"
    )

    desenho.rectangle(
        (15, 18, 49, 52),
        outline="white",
        width=4
    )

    desenho.line(
        (15, 28, 49, 28),
        fill="white",
        width=4
    )

    desenho.line(
        (25, 12, 25, 22),
        fill="white",
        width=4
    )

    desenho.line(
        (39, 12, 39, 22),
        fill="white",
        width=4
    )

    return imagem


# ============================================================
# COMUNICAÇÃO TRAY -> TKINTER
# ============================================================

def pedir_abrir_agenda(icon=None, item=None):

    fila_tray.put(
        "abrir"
    )


def pedir_sair_agenda(icon=None, item=None):

    fila_tray.put(
        "sair"
    )


def verificar_fila_tray():

    try:

        while True:

            comando = fila_tray.get_nowait()

            if comando == "abrir":

                mostrar_janela()

            elif comando == "sair":

                sair_programa()

    except queue.Empty:

        pass

    if janela.winfo_exists():

        janela.after(
            100,
            verificar_fila_tray
        )


# ============================================================
# MOSTRAR / ESCONDER AGENDA
# ============================================================

def mostrar_janela():

    janela.deiconify()

    janela.state(
        "normal"
    )

    janela.lift()

    janela.attributes(
        "-topmost",
        True
    )

    janela.after(
        200,
        lambda: janela.attributes(
            "-topmost",
            False
        )
    )

    janela.focus_force()


def esconder_janela():

    janela.withdraw()


# ============================================================
# SAIR
# ============================================================

def sair_programa():

    global tray_icon

    if tray_icon is not None:

        try:
            tray_icon.stop()
        except Exception:
            pass

        tray_icon = None

    janela.destroy()


# ============================================================
# TRAY
# ============================================================

def executar_tray():

    global tray_icon

    menu = pystray.Menu(

        pystray.MenuItem(
            "Abrir Minha Agenda",
            pedir_abrir_agenda,
            default=True
        ),

        pystray.MenuItem(
            "Sair",
            pedir_sair_agenda
        )
    )

    tray_icon = pystray.Icon(
        "Minha Agenda",
        criar_icone_tray(),
        "Minha Agenda",
        menu
    )

    tray_icon.run()


# ============================================================
# INTEGRAÇÃO COM O NÚCLEO COMPARTILHADO
# ============================================================

# A versão do Windows passa a usar o mesmo núcleo de banco
# que será utilizado como base para a futura versão Android.
conectar = agenda_core.conectar
criar_banco = agenda_core.criar_banco


# ============================================================
# CRIAÇÃO DA JANELA
# ============================================================

criar_banco()

janela = tk.Tk()

janela.title(
    "Minha Agenda"
)

janela.geometry(
    "1500x950"
)

janela.minsize(
    1300,
    850
)


# ============================================================
# ESTILO
# ============================================================

estilo = ttk.Style()

try:

    estilo.theme_use(
        "clam"
    )

except tk.TclError:

    pass


estilo.configure(
    "Treeview",
    font=(
        "Arial",
        13
    ),
    rowheight=40
)

estilo.configure(
    "Treeview.Heading",
    font=(
        "Arial",
        13,
        "bold"
    ),
    padding=(
        10,
        10
    )
)


# ============================================================
# TÍTULO
# ============================================================

titulo = tk.Label(
    janela,
    text="MINHA AGENDA",
    font=(
        "Arial",
        26,
        "bold"
    )
)

titulo.pack(
    pady=(
        18,
        3
    )
)


subtitulo = tk.Label(
    janela,
    text="Compromissos e aniversários",
    font=(
        "Arial",
        12
    )
)

subtitulo.pack(
    pady=(
        0,
        12
    )
)


# ============================================================
# FORMULÁRIO
# ============================================================

frame_formulario = tk.LabelFrame(
    janela,
    text="Novo evento",
    padx=18,
    pady=12,
    font=(
        "Arial",
        11,
        "bold"
    )
)

frame_formulario.pack(
    fill="x",
    padx=25,
    pady=5
)


# ============================================================
# TIPO
# ============================================================

tk.Label(
    frame_formulario,
    text="Tipo:",
    font=("Arial", 11)
).grid(
    row=0,
    column=0,
    sticky="w",
    padx=5,
    pady=6
)


tipo_evento = ttk.Combobox(
    frame_formulario,
    values=[
        "Compromisso",
        "Aniversário"
    ],
    state="readonly",
    width=25,
    font=("Arial", 11)
)

tipo_evento.grid(
    row=0,
    column=1,
    sticky="w",
    padx=5,
    pady=6
)

tipo_evento.set(
    "Compromisso"
)

tipo_evento.bind(
    "<<ComboboxSelected>>",
    alterar_tipo
)


# ============================================================
# NOME
# ============================================================

tk.Label(
    frame_formulario,
    text="Compromisso / Nome:",
    font=("Arial", 11)
).grid(
    row=1,
    column=0,
    sticky="w",
    padx=5,
    pady=6
)


entrada_nome = tk.Entry(
    frame_formulario,
    width=72,
    font=("Arial", 11)
)

entrada_nome.grid(
    row=1,
    column=1,
    columnspan=5,
    sticky="w",
    padx=5,
    pady=6
)


# ============================================================
# DATA
# ============================================================

texto_data = tk.Label(
    frame_formulario,
    text="Data:",
    font=("Arial", 11)
)

texto_data.grid(
    row=2,
    column=0,
    sticky="w",
    padx=5,
    pady=6
)


entrada_data = tk.Entry(
    frame_formulario,
    width=22,
    font=("Arial", 11)
)

entrada_data.grid(
    row=2,
    column=1,
    sticky="w",
    padx=5,
    pady=6
)

entrada_data.insert(
    0,
    "DD/MM/AAAA"
)

entrada_data.bind(
    "<FocusIn>",
    foco_data
)

entrada_data.bind(
    "<FocusOut>",
    sair_data
)


# ============================================================
# HORÁRIO
# ============================================================

texto_horario = tk.Label(
    frame_formulario,
    text="Horário:",
    font=("Arial", 11)
)

texto_horario.grid(
    row=2,
    column=2,
    sticky="w",
    padx=30,
    pady=6
)


entrada_horario = tk.Entry(
    frame_formulario,
    width=15,
    font=("Arial", 11)
)

entrada_horario.grid(
    row=2,
    column=3,
    sticky="w",
    padx=5,
    pady=6
)

entrada_horario.insert(
    0,
    "HH:MM"
)

entrada_horario.bind(
    "<FocusIn>",
    foco_horario
)

entrada_horario.bind(
    "<FocusOut>",
    sair_horario
)


# ============================================================
# HORAS ANTES
# ============================================================

tk.Label(
    frame_formulario,
    text="Horas antes:",
    font=("Arial", 11)
).grid(
    row=3,
    column=0,
    sticky="w",
    padx=5,
    pady=6
)


entrada_aviso_horas = tk.Entry(
    frame_formulario,
    width=22,
    font=("Arial", 11)
)

entrada_aviso_horas.grid(
    row=3,
    column=1,
    sticky="w",
    padx=5,
    pady=6
)

entrada_aviso_horas.insert(
    0,
    "24"
)


# ============================================================
# DIAS ANTES
# ============================================================

tk.Label(
    frame_formulario,
    text="Dias antes (aniversário):",
    font=("Arial", 11)
).grid(
    row=3,
    column=2,
    sticky="w",
    padx=30,
    pady=6
)


entrada_aviso_dias = tk.Entry(
    frame_formulario,
    width=15,
    font=("Arial", 11)
)

entrada_aviso_dias.grid(
    row=3,
    column=3,
    sticky="w",
    padx=5,
    pady=6
)


# ============================================================
# HORÁRIO DO AVISO
# ============================================================

tk.Label(
    frame_formulario,
    text="Horário do aviso:",
    font=("Arial", 11)
).grid(
    row=4,
    column=0,
    sticky="w",
    padx=5,
    pady=6
)


entrada_horario_aviso = tk.Entry(
    frame_formulario,
    width=22,
    font=("Arial", 11)
)

entrada_horario_aviso.grid(
    row=4,
    column=1,
    sticky="w",
    padx=5,
    pady=6
)


# ============================================================
# DETALHE
# ============================================================

tk.Label(
    frame_formulario,
    text="Detalhe:",
    font=("Arial", 11)
).grid(
    row=5,
    column=0,
    sticky="nw",
    padx=5,
    pady=6
)


entrada_detalhe = tk.Text(
    frame_formulario,
    width=80,
    height=4,
    font=("Arial", 11)
)

entrada_detalhe.grid(
    row=5,
    column=1,
    columnspan=5,
    sticky="w",
    padx=5,
    pady=6
)


# ============================================================
# BOTÕES DO FORMULÁRIO
# ============================================================

frame_botoes = tk.Frame(
    frame_formulario
)

frame_botoes.grid(
    row=6,
    column=1,
    columnspan=5,
    sticky="w",
    padx=5,
    pady=8
)


botao_cadastrar = tk.Button(
    frame_botoes,
    text="CADASTRAR",
    command=salvar_evento,
    width=22,
    height=2,
    font=("Arial", 11)
)

botao_cadastrar.pack(
    side="left",
    padx=(0, 10)
)


botao_cancelar = tk.Button(
    frame_botoes,
    text="CANCELAR EDIÇÃO",
    command=limpar_campos,
    width=22,
    height=2,
    font=("Arial", 11),
    state="disabled"
)

botao_cancelar.pack(
    side="left"
)


# ============================================================
# PESQUISA
# ============================================================

frame_pesquisa = tk.Frame(
    janela
)

frame_pesquisa.pack(
    fill="x",
    padx=25,
    pady=(
        12,
        5
    )
)


tk.Label(
    frame_pesquisa,
    text="🔎 Pesquisar:",
    font=("Arial", 12)
).pack(
    side="left",
    padx=(0, 10)
)


entrada_pesquisa = tk.Entry(
    frame_pesquisa,
    width=50,
    font=("Arial", 12)
)

entrada_pesquisa.pack(
    side="left"
)

entrada_pesquisa.bind(
    "<KeyRelease>",
    filtrar_eventos
)


botao_limpar_pesquisa = tk.Button(
    frame_pesquisa,
    text="LIMPAR PESQUISA",
    command=limpar_pesquisa,
    width=18,
    height=1,
    font=("Arial", 10)
)

botao_limpar_pesquisa.pack(
    side="left",
    padx=10
)


# ============================================================
# BOTÕES DA LISTA
# ============================================================

frame_acoes = tk.Frame(
    janela
)

frame_acoes.pack(
    pady=10
)


botao_editar = tk.Button(
    frame_acoes,
    text="✏️ EDITAR SELECIONADO",
    command=editar_evento,
    width=25,
    height=2,
    font=("Arial", 11)
)

botao_editar.pack(
    side="left",
    padx=6
)


botao_excluir = tk.Button(
    frame_acoes,
    text="🗑️ EXCLUIR SELECIONADO",
    command=excluir_evento,
    width=25,
    height=2,
    font=("Arial", 11)
)

botao_excluir.pack(
    side="left",
    padx=6
)



# ============================================================
# LISTA
# ============================================================

frame_lista = tk.LabelFrame(
    janela,
    text="Eventos cadastrados",
    padx=10,
    pady=10,
    font=(
        "Arial",
        11,
        "bold"
    )
)

frame_lista.pack(
    fill="both",
    expand=True,
    padx=25,
    pady=5
)


colunas = (
    "id",
    "tipo",
    "nome",
    "data",
    "horario",
    "regra",
    "proximo"
)


tabela = ttk.Treeview(
    frame_lista,
    columns=colunas,
    show="headings",
    selectmode="browse"
)


tabela.heading(
    "id",
    text="ID"
)

tabela.heading(
    "tipo",
    text="Tipo"
)

tabela.heading(
    "nome",
    text="Nome / Compromisso"
)

tabela.heading(
    "data",
    text="Data"
)

tabela.heading(
    "horario",
    text="Horário"
)

tabela.heading(
    "regra",
    text="Regra de aviso"
)

tabela.heading(
    "proximo",
    text="Próximo aviso"
)


tabela.column(
    "id",
    width=0,
    minwidth=0,
    stretch=False
)

tabela.column(
    "tipo",
    width=160,
    minwidth=150,
    anchor="center"
)

tabela.column(
    "nome",
    width=430,
    minwidth=350,
    anchor="w"
)

tabela.column(
    "data",
    width=140,
    minwidth=120,
    anchor="center"
)

tabela.column(
    "horario",
    width=130,
    minwidth=110,
    anchor="center"
)

tabela.column(
    "regra",
    width=250,
    minwidth=210,
    anchor="center"
)

tabela.column(
    "proximo",
    width=270,
    minwidth=230,
    anchor="center"
)


tabela.pack(
    side="left",
    fill="both",
    expand=True
)


# ============================================================
# BARRA VERTICAL
# ============================================================

barra_vertical = ttk.Scrollbar(
    frame_lista,
    orient="vertical",
    command=tabela.yview
)

barra_vertical.pack(
    side="right",
    fill="y"
)

tabela.configure(
    yscrollcommand=barra_vertical.set
)


# ============================================================
# BARRA HORIZONTAL
# ============================================================

barra_horizontal = ttk.Scrollbar(
    frame_lista,
    orient="horizontal",
    command=tabela.xview
)

barra_horizontal.pack(
    side="bottom",
    fill="x"
)

tabela.configure(
    xscrollcommand=barra_horizontal.set
)


# ============================================================
# INICIALIZAÇÃO
# ============================================================

carregar_eventos()

alterar_tipo()

janela.after(
    1000,
    verificar_lembretes
)

# Verifica continuamente os comandos vindos do ícone
janela.after(
    100,
    verificar_fila_tray
)


# ============================================================
# BOTÃO X
# ============================================================

janela.protocol(
    "WM_DELETE_WINDOW",
    esconder_janela
)


# ============================================================
# INICIA O ÍCONE
# ============================================================

threading.Thread(
    target=executar_tray,
    daemon=True
).start()


# ============================================================
# LOOP PRINCIPAL
# ============================================================

janela.mainloop()