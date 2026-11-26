from utils import escrever_log


def consolidar_dados(dados_lidos):
    resultado_final = {}

    escrever_log("Iniciando consolidação de dados.")

    for cpf, info in dados_lidos.items():

        cpf = str(cpf).strip()

        declarando = info["declarando_por"]
        transmitido = info["transmitido_por"]
        pcs_declarando = info["pcs_declarando"]
        pcs_transmitido = info["pcs_transmitido"]

        status = ""
        conflito = False

        if transmitido:
            if len(pcs_transmitido) > 1:
                status = "CONFLITO - Transmitida duplicada"
                conflito = True
            else:
                status = "Transmitida"

        elif declarando:
            if len(pcs_declarando) > 1:
                status = "CONFLITO - Múltiplos PCs"
                conflito = True
            else:
                status = "Em andamento"
        else:
            status = "Não iniciada"

        resultado_final[cpf] = {
            "nome": info.get("nome"),
            "status": status,
            "feita_por": ";".join(sorted(declarando)),
            "transmitida_por": ";".join(sorted(transmitido)),
            "data_transmissao": info.get("data_transmissao"),
            "conflito": conflito
        }

    escrever_log("Consolidação finalizada.")
    return resultado_final
