import os
import pandas as pd
from utils import limpar_cpf, formatar_cpf
from config import ARQ_PLANILHA_FINAL, CSV


def atualizar_planilha(dados_consolidados):

    if not os.path.exists(ARQ_PLANILHA_FINAL):
        df = pd.DataFrame(columns=[
            "CPF", "Nome", "Status", "Feita por", "Transmitida por", "Data Transmissão"
        ])
        df.to_excel(ARQ_PLANILHA_FINAL, index=False)

    df = pd.read_excel(ARQ_PLANILHA_FINAL, dtype=str)

    # garante colunas
    for col in ["CPF", "Nome", "Status", "Feita por", "Transmitida por", "Data Transmissão"]:
        if col not in df.columns:
            df[col] = ""

    # cria coluna técnica
    df["CPF_LIMPO"] = df["CPF"].apply(limpar_cpf)

    df_index = {cpf: i for i, cpf in enumerate(df["CPF_LIMPO"])}

    for cpf, info in dados_consolidados.items():

        cpf = limpar_cpf(cpf)
        cpf_formatado = formatar_cpf(cpf)

        data_tx = info.get("data_transmissao")
        data_formatada = (
            data_tx.strftime("%d/%m/%Y %H:%M:%S")
            if data_tx else ""
        )

        nome = info.get("nome", "")

        if cpf in df_index:
            i = df_index[cpf]

            # Obter valores atuais (tratar NaN e 'nan' string)
            def obter_valor_atual(coluna):
                val = df.at[i, coluna]
                return str(val).strip() if pd.notna(val) and str(val).strip().lower() != "nan" else ""

            nome_atual = obter_valor_atual("Nome")
            status_atual = obter_valor_atual("Status")
            feita_por_atual = obter_valor_atual("Feita por")
            transmitida_por_atual = obter_valor_atual("Transmitida por")
            data_atual = obter_valor_atual("Data Transmissão")

            # 1) Mesclar Nome (se não tiver nome novo, usa o atual)
            nome_final = nome if nome else nome_atual

            # 2) Mesclar usuários (união)
            def merge_users(u1, u2):
                s = set(x.strip() for x in u1.split(";")) | set(x.strip() for x in u2.split(";"))
                s = {x for x in s if x}
                return ";".join(sorted(s))

            feita_por_final = merge_users(feita_por_atual, info["feita_por"])
            transmitida_por_final = merge_users(transmitida_por_atual, info["transmitida_por"])

            # 3) Lógica de Status (não rebaixar status se perdemos acesso a uma máquina)
            status_novo = info["status"]
            pesos = {
                "Não iniciada": 0,
                "Em andamento": 1,
                "CONFLITO - Múltiplos PCs": 2,
                "Transmitida": 3,
                "CONFLITO - Transmitida duplicada": 4
            }
            p_atual = pesos.get(status_atual, -1)
            p_novo = pesos.get(status_novo, -1)

            if p_novo >= p_atual:
                status_final = status_novo
            else:
                status_final = status_atual

            # 4) Data de Transmissão
            data_final = data_formatada
            # Se não há data nova ou o status sofreu regressão por falta de leitura da rede, mantém a atual
            if (not data_final) or (p_novo < p_atual):
                if data_atual:
                    data_final = data_atual

            # 🔥 atualiza a linha
            df.at[i, "CPF"] = cpf_formatado
            df.at[i, "Nome"] = nome_final
            df.at[i, "Status"] = status_final
            df.at[i, "Feita por"] = feita_por_final
            df.at[i, "Transmitida por"] = transmitida_por_final
            df.at[i, "Data Transmissão"] = data_final

        else:
            nova_linha = {
                "CPF": cpf_formatado,
                "Nome": nome,
                "Status": info["status"],
                "Feita por": info["feita_por"],
                "Transmitida por": info["transmitida_por"],
                "Data Transmissão": data_formatada
            }

            df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)

    df.drop(columns=["CPF_LIMPO"], inplace=True)

    print("Salvando planilha...")
    df.to_excel(ARQ_PLANILHA_FINAL, index=False)
    df.to_csv(CSV, index=False)
    print("Planilha salva com sucesso!")

    return ARQ_PLANILHA_FINAL
