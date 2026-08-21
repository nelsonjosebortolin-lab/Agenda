from agenda_core import conectar, listar_eventos_ordenados


print("=" * 50)
print("TESTE DO NÚCLEO DA AGENDA")
print("=" * 50)

try:
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM eventos"
    )

    quantidade = cursor.fetchone()[0]

    conexao.close()

    print()
    print("Banco de dados acessado com sucesso!")
    print(f"Quantidade de eventos cadastrados: {quantidade}")

    print()
    print("Eventos encontrados:")

    eventos = listar_eventos_ordenados()

    if not eventos:
        print("Nenhum evento cadastrado.")

    else:
        for evento in eventos:
            print(
                f"- {evento['nome']} | "
                f"{evento['data']} | "
                f"{evento['horario'] or '-'}"
            )

    print()
    print("TESTE CONCLUÍDO COM SUCESSO.")

except Exception as erro:

    print()
    print("ERRO NO TESTE:")
    print(erro)