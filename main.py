#main.py
from leitores import varrer_maquinas
from consolidacao import consolidar_dados
from planilha import atualizar_planilha
from utils import escrever_log


def main():
    escrever_log("=== INÍCIO DA EXECUÇÃO ===")

    dados_lidos = varrer_maquinas()
    dados_consolidados = consolidar_dados(dados_lidos)

    print("\nESTRUTURA (amostra):")
    for k, v in list(dados_consolidados.items())[:5]:
        print(k, v["status"], v["data_transmissao"])

    arquivo_gerado = atualizar_planilha(dados_consolidados)

    print(f"\nPlanilha gerada: {arquivo_gerado}")

    escrever_log("Execução finalizada com sucesso.")
    escrever_log("================================\n")


if __name__ == "__main__":
    main()
