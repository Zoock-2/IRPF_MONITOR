import os
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

from config import (
    ARQ_COMPUTADORES,
    PASTA_BASE_RFB,
    ANO_IRPF,
    SUBPASTA_DADOS,
    SUBPASTA_TRANSMITIDAS
)

from utils import (
    escrever_log,
    escrever_log_por_usuario,
    extrair_cpf_do_xml,
    extrair_nome_do_xml
)


def ler_computadores():
    try:
        df = pd.read_excel(ARQ_COMPUTADORES)
        escrever_log("[INFO] Planilha de computadores carregada.")
        return df
    except Exception as e:
        escrever_log(f"[ERRO] Ler planilha: {e}")
        return None


def montar_caminho_base(computador):
    return rf"\\{computador}\C$\{PASTA_BASE_RFB}\IRPF{ANO_IRPF}"


def gerar_log_maquina(nome_usuario, computador, dados_local):

    cpfs_declarando = sorted([
        cpf for cpf, info in dados_local.items()
        if info["pcs_declarando"]
    ])

    cpfs_transmitidos = sorted([
        cpf for cpf, info in dados_local.items()
        if info["pcs_transmitido"]
    ])

    total_declarando = len(cpfs_declarando)
    total_transmitidos = len(cpfs_transmitidos)

    linhas = []
    linhas.append(f"\n=== LOG DA MÁQUINA: {computador or 'CAMINHO CUSTOM'} ===")
    linhas.append(f"Usuário responsável: {nome_usuario}")
    linhas.append(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")

    linhas.append("CPFs encontrados em aplicacao/dados:")
    linhas.extend(cpfs_declarando or ["Nenhum"])

    linhas.append("\nCPFs transmitidos:")
    linhas.extend(cpfs_transmitidos or ["Nenhum"])

    linhas.append(f"\nTotal declarando: {total_declarando}")
    linhas.append(f"Total transmitidos: {total_transmitidos}")
    linhas.append("\n" + "=" * 50 + "\n")

    msg = "\n".join(linhas)
    escrever_log_por_usuario(nome_usuario, msg)
    escrever_log(msg)


def processar_maquina(nome_usuario, computador, caminho_custom=None):

    dados_local = {}

    # 🔥 define caminho base
    if caminho_custom:
        caminho_base = caminho_custom
        escrever_log(f"[INFO] Varrendo caminho custom: {nome_usuario} -> {caminho_base}")
    else:
        caminho_base = montar_caminho_base(computador)
        escrever_log(f"[INFO] Varrendo {computador} ({nome_usuario})")

    pasta_dados = os.path.join(caminho_base, SUBPASTA_DADOS)
    pasta_transmitidas = os.path.join(caminho_base, SUBPASTA_TRANSMITIDAS)

    # ================= DADOS =================
    try:
        if os.path.exists(pasta_dados):

            for pasta_cpf in os.listdir(pasta_dados):

                caminho_pasta = os.path.join(pasta_dados, pasta_cpf)
                if not os.path.isdir(caminho_pasta):
                    continue

                for arquivo in os.listdir(caminho_pasta):
                    if arquivo.lower().endswith(".xml"):

                        caminho_xml = os.path.join(caminho_pasta, arquivo)

                        cpf = extrair_cpf_do_xml(caminho_xml, pasta_cpf)
                        nome = extrair_nome_do_xml(caminho_xml)

                        if cpf:
                            cpf = str(cpf).strip()

                            if cpf not in dados_local:
                                dados_local[cpf] = {
                                    "nome": nome,
                                    "declarando_por": set(),
                                    "transmitido_por": set(),
                                    "pcs_declarando": set(),
                                    "pcs_transmitido": set(),
                                    "data_transmissao": None
                                }

                            if nome and not dados_local[cpf].get("nome"):
                                dados_local[cpf]["nome"] = nome

                            dados_local[cpf]["declarando_por"].add(nome_usuario)
                            dados_local[cpf]["pcs_declarando"].add(computador or "CAMINHO_CUSTOM")

                        break  # mantém lógica original

    except Exception as e:
        escrever_log(f"[ERRO DADOS] {computador or 'CUSTOM'}: {e}")

    # ================= TRANSMITIDAS =================
    try:
        if os.path.exists(pasta_transmitidas):

            for arquivo in os.listdir(pasta_transmitidas):

                if arquivo.lower().endswith((".dec", ".rec", ".re")):

                    caminho_arquivo = os.path.join(pasta_transmitidas, arquivo)
                    data_arquivo = datetime.fromtimestamp(
                        os.path.getmtime(caminho_arquivo)
                    )

                    match = re.search(r'\d{11}', arquivo)
                    cpf = match.group(0) if match else None

                    if cpf:
                        cpf = str(cpf).strip()

                        if cpf not in dados_local:
                            dados_local[cpf] = {
                                "nome": None,
                                "declarando_por": set(),
                                "transmitido_por": set(),
                                "pcs_declarando": set(),
                                "pcs_transmitido": set(),
                                "data_transmissao": None
                            }

                        dados_local[cpf]["transmitido_por"].add(nome_usuario)
                        dados_local[cpf]["pcs_transmitido"].add(computador or "CAMINHO_CUSTOM")

                        atual = dados_local[cpf]["data_transmissao"]

                        if not atual or data_arquivo > atual:
                            dados_local[cpf]["data_transmissao"] = data_arquivo

    except Exception as e:
        escrever_log(f"[ERRO TRANSMITIDAS] {computador or 'CUSTOM'}: {e}")

    gerar_log_maquina(nome_usuario, computador, dados_local)

    return dados_local


def varrer_maquinas():

    df = ler_computadores()
    if df is None:
        return {}

    maquinas = []

    for _, row in df.iterrows():
        nome = str(row["Nome"]).strip()

        computador = ""
        if "Computador" in df.columns and pd.notna(row["Computador"]):
            computador = str(row["Computador"]).strip()

        caminho_custom = ""
        if "Caminho" in df.columns and pd.notna(row["Caminho"]):
            caminho_custom = str(row["Caminho"]).strip()

        maquinas.append((nome, computador, caminho_custom))

    dados_finais = {}

    with ThreadPoolExecutor(max_workers=6) as executor:

        futures = [
            executor.submit(processar_maquina, n, pc, caminho)
            for n, pc, caminho in maquinas
        ]

        for future in as_completed(futures):

            resultado = future.result()

            for cpf, info in resultado.items():

                if cpf not in dados_finais:
                    dados_finais[cpf] = {
                        "nome": info.get("nome"),
                        "declarando_por": set(),
                        "transmitido_por": set(),
                        "pcs_declarando": set(),
                        "pcs_transmitido": set(),
                        "data_transmissao": None
                    }

                # mantém nome
                if not dados_finais[cpf].get("nome") and info.get("nome"):
                    dados_finais[cpf]["nome"] = info.get("nome")

                nova = info["data_transmissao"]
                atual = dados_finais[cpf]["data_transmissao"]

                if nova and (not atual or nova > atual):
                    dados_finais[cpf]["data_transmissao"] = nova

                dados_finais[cpf]["declarando_por"].update(info["declarando_por"])
                dados_finais[cpf]["transmitido_por"].update(info["transmitido_por"])
                dados_finais[cpf]["pcs_declarando"].update(info["pcs_declarando"])
                dados_finais[cpf]["pcs_transmitido"].update(info["pcs_transmitido"])

    escrever_log("\n[INFO] Varredura finalizada.\n")

    return dados_finais
