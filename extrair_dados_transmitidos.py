import os
# Prevenir erro de alocação de memória do OpenBLAS com pandas/numpy
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

import re
import xml.etree.ElementTree as ET
import pandas as pd

from config import (
    ARQ_PLANILHA_FINAL,
    PASTA_BASE_RFB,
    ANO_IRPF,
    SUBPASTA_DADOS,
    SUBPASTA_TRANSMITIDAS
)
from utils import (
    limpar_cpf,
    formatar_cpf
)

def ler_clientes_transmitidos():
    """Lê a planilha final e retorna um dicionário de CPFs que estão 'Transmitida'"""
    try:
        df = pd.read_excel(ARQ_PLANILHA_FINAL, dtype=str)
        clientes = {}
        for _, row in df.iterrows():
            status = str(row.get("Status", "")).strip().lower()
            if "transmitida" in status:
                cpf = str(row.get("CPF", ""))
                nome = str(row.get("Nome", ""))
                cpf_limpo = limpar_cpf(cpf)
                if cpf_limpo:
                    clientes[cpf_limpo] = {
                        "Nome": nome,
                        "CPF": formatar_cpf(cpf_limpo),
                        "totalExercicioAnterior": "",
                        "totalExercicioAtual": "",
                        "saldoImpostoPagar": "",
                        "dividasOnusReaisExercicioAnterior": "",
                        "dividasOnusReaisExercicioAtual": ""
                    }
        return clientes
    except Exception as e:
        print(f"[ERRO] Falha ao ler a planilha de clientes: {e}")
        return None

def montar_caminhos_base(computador, caminho_custom=None):
    caminhos = []
    base = caminho_custom if caminho_custom else rf"\\{computador}\C$\{PASTA_BASE_RFB}\IRPF{ANO_IRPF}"
    caminhos.append(os.path.join(base, SUBPASTA_DADOS))
    caminhos.append(os.path.join(base, SUBPASTA_TRANSMITIDAS))
    return caminhos

def extrair_dados_xml(caminho_xml):
    """Extrai bens, dividas e saldo do XML"""
    dados = {
        "totalExercicioAnterior": None,
        "totalExercicioAtual": None,
        "saldoImpostoPagar": None,
        "dividasOnusReaisExercicioAnterior": None,
        "dividasOnusReaisExercicioAtual": None,
        "numReciboTransmitido": None
    }
    try:
        tree = ET.parse(caminho_xml)
        root = tree.getroot()
        
        if "numReciboTransmitido" in root.attrib:
            dados["numReciboTransmitido"] = root.attrib["numReciboTransmitido"]
            
        for elem in root.iter():
            tag_local = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            
            if "numReciboTransmitido" in elem.attrib:
                dados["numReciboTransmitido"] = elem.attrib["numReciboTransmitido"]
                
            if tag_local.lower() == "bens":
                if "totalExercicioAnterior" in elem.attrib:
                    dados["totalExercicioAnterior"] = elem.attrib["totalExercicioAnterior"]
                if "totalExercicioAtual" in elem.attrib:
                    dados["totalExercicioAtual"] = elem.attrib["totalExercicioAtual"]
            
            if "dividasOnusReaisExercicioAnterior" in elem.attrib:
                dados["dividasOnusReaisExercicioAnterior"] = elem.attrib["dividasOnusReaisExercicioAnterior"]
            elif tag_local.lower() in ("dividasonusreais", "dividas") and "totalExercicioAnterior" in elem.attrib:
                dados["dividasOnusReaisExercicioAnterior"] = elem.attrib["totalExercicioAnterior"]
                
            if "dividasOnusReaisExercicioAtual" in elem.attrib:
                dados["dividasOnusReaisExercicioAtual"] = elem.attrib["dividasOnusReaisExercicioAtual"]
            elif tag_local.lower() in ("dividasonusreais", "dividas") and "totalExercicioAtual" in elem.attrib:
                dados["dividasOnusReaisExercicioAtual"] = elem.attrib["totalExercicioAtual"]

            # Extract Saldo Imposto a Pagar
            if tag_local.lower() == "saldoimpostopagar" and elem.text:
                dados["saldoImpostoPagar"] = elem.text.strip()
            for attr_name, attr_val in elem.attrib.items():
                if attr_name.lower() == "saldoimpostopagar":
                    dados["saldoImpostoPagar"] = attr_val.strip()
    except Exception as e:
        # Fallback via regex
        try:
            with open(caminho_xml, "r", encoding="latin-1") as f:
                conteudo = f.read()
            
            if dados["numReciboTransmitido"] is None:
                match_recibo = re.search(r'numReciboTransmitido\s*=\s*["\']([^"\']*)["\']', conteudo, re.IGNORECASE)
                if match_recibo:
                    dados["numReciboTransmitido"] = match_recibo.group(1).strip()

            if dados["saldoImpostoPagar"] is None:
                match_saldo = re.search(r'saldoImpostoPagar\s*=\s*["\']([^"\']*)["\']', conteudo, re.IGNORECASE)
                if match_saldo:
                    dados["saldoImpostoPagar"] = match_saldo.group(1).strip()
            
            if dados["totalExercicioAnterior"] is None or dados["totalExercicioAtual"] is None:
                match_bens = re.search(r'<bens[^>]*totalExercicioAnterior=["\']([^"\']*)["\'][^>]*totalExercicioAtual=["\']([^"\']*)["\']', conteudo, re.IGNORECASE)
                if match_bens:
                    dados["totalExercicioAnterior"] = match_bens.group(1)
                    dados["totalExercicioAtual"] = match_bens.group(2)

            if dados["dividasOnusReaisExercicioAnterior"] is None:
                match_div_anterior = re.search(r'dividasOnusReaisExercicioAnterior\s*=\s*["\']([^"\']*)["\']', conteudo, re.IGNORECASE)
                if match_div_anterior:
                    dados["dividasOnusReaisExercicioAnterior"] = match_div_anterior.group(1).strip()
                else:
                    match_div_tag_ant = re.search(r'<dividasOnusReais[^>]*totalExercicioAnterior=["\']([^"\']*)["\']', conteudo, re.IGNORECASE)
                    if match_div_tag_ant:
                        dados["dividasOnusReaisExercicioAnterior"] = match_div_tag_ant.group(1).strip()

            if dados["dividasOnusReaisExercicioAtual"] is None:
                match_div_atual = re.search(r'dividasOnusReaisExercicioAtual\s*=\s*["\']([^"\']*)["\']', conteudo, re.IGNORECASE)
                if match_div_atual:
                    dados["dividasOnusReaisExercicioAtual"] = match_div_atual.group(1).strip()
                else:
                    match_div_tag_atu = re.search(r'<dividasOnusReais[^>]*totalExercicioAtual=["\']([^"\']*)["\']', conteudo, re.IGNORECASE)
                    if match_div_tag_atu:
                        dados["dividasOnusReaisExercicioAtual"] = match_div_tag_atu.group(1).strip()

        except Exception:
            pass

    return dados

def processar_maquina(nome_usuario, computador, caminho_custom, cpfs_alvo):
    resultados = {}
    caminhos = montar_caminhos_base(computador, caminho_custom)

    for pasta_base in caminhos:
        try:
            if not os.path.exists(pasta_base):
                continue
            
            for item in os.listdir(pasta_base):
                caminho_item = os.path.join(pasta_base, item)
                
                # Se for arquivo xml solto (às vezes na pasta transmitidas)
                if os.path.isfile(caminho_item) and item.lower().endswith(".xml"):
                    cpf_arquivo = limpar_cpf(item)
                    cpf_encontrado = None
                    if cpf_arquivo:
                        for alvo in cpfs_alvo:
                            if alvo in cpf_arquivo:
                                cpf_encontrado = alvo
                                break
                    
                    if cpf_encontrado:
                        dados_xml = extrair_dados_xml(caminho_item)
                        if dados_xml.get("numReciboTransmitido") and dados_xml["numReciboTransmitido"] != "0000000000":
                            if any(v is not None for k, v in dados_xml.items() if k != "numReciboTransmitido"):
                                resultados[cpf_encontrado] = dados_xml

                # Se for pasta (padrão em aplicacao/dados)
                if os.path.isdir(caminho_item):
                    cpf_pasta = limpar_cpf(item)
                    
                    # Só processa se o CPF está nos nossos alvos
                    if cpf_pasta in cpfs_alvo:
                        xmls_na_pasta = [arq for arq in os.listdir(caminho_item) if arq.lower().endswith(".xml")]
                        if not xmls_na_pasta:
                            continue

                        xml_escolhido = None
                        for arq in xmls_na_pasta:
                            caminho_xml = os.path.join(caminho_item, arq)
                            try:
                                with open(caminho_xml, 'r', encoding='latin-1') as f:
                                    inicio = f.read(500)
                                if "DeclaracaoIRPF" in inicio or "IRPF" in inicio:
                                    dados_check = extrair_dados_xml(caminho_xml)
                                    if dados_check.get("numReciboTransmitido") and dados_check["numReciboTransmitido"] != "0000000000":
                                        xml_escolhido = caminho_xml
                                        break
                            except Exception:
                                pass

                        if xml_escolhido:
                            dados_xml = extrair_dados_xml(xml_escolhido)
                            # Se achou algo útil, guarda
                            if any(v is not None for k, v in dados_xml.items() if k != "numReciboTransmitido"):
                                resultados[cpf_pasta] = dados_xml
                            
        except Exception as e:
            pass

    return resultados

def main():
    print("=== INICIANDO EXTRAÇÃO DE DADOS DOS TRANSMITIDOS ===")
    
    clientes_alvo = ler_clientes_transmitidos()
    if not clientes_alvo:
        print("[ERRO] Nenhum cliente transmitido encontrado ou erro ao ler planilha.")
        return
        
    print(f"Encontrados {len(clientes_alvo)} clientes com status 'Transmitida'.")

    # --- BUSCA APENAS NA CONSOLIDAÇÃO ---
    pasta_consolidacao = r"H:\TI - INFORMATICA\Publico\IRPF2026\consolidação\IRPF2026"
    print(f"\nBuscando dados na pasta de consolidação:\n{pasta_consolidacao}")
    
    resultado_consolida = processar_maquina("Consolidacao", "", pasta_consolidacao, clientes_alvo)
    
    for cpf, dados in resultado_consolida.items():
        if cpf in clientes_alvo:
            if dados["totalExercicioAnterior"] and not clientes_alvo[cpf]["totalExercicioAnterior"]:
                clientes_alvo[cpf]["totalExercicioAnterior"] = dados["totalExercicioAnterior"]
            if dados["totalExercicioAtual"] and not clientes_alvo[cpf]["totalExercicioAtual"]:
                clientes_alvo[cpf]["totalExercicioAtual"] = dados["totalExercicioAtual"]
            if dados["saldoImpostoPagar"] and not clientes_alvo[cpf]["saldoImpostoPagar"]:
                clientes_alvo[cpf]["saldoImpostoPagar"] = dados["saldoImpostoPagar"]
            if dados["dividasOnusReaisExercicioAnterior"] and not clientes_alvo[cpf]["dividasOnusReaisExercicioAnterior"]:
                clientes_alvo[cpf]["dividasOnusReaisExercicioAnterior"] = dados["dividasOnusReaisExercicioAnterior"]
            if dados["dividasOnusReaisExercicioAtual"] and not clientes_alvo[cpf]["dividasOnusReaisExercicioAtual"]:
                clientes_alvo[cpf]["dividasOnusReaisExercicioAtual"] = dados["dividasOnusReaisExercicioAtual"]

    # Prepara os dados para salvar
    lista_final = list(clientes_alvo.values())
    
    # Renomeia as chaves para colunas mais bonitas
    lista_para_df = []
    for item in lista_final:
        lista_para_df.append({
            "Nome": item["Nome"],
            "CPF": item["CPF"],
            "Bens - Exercicio Anterior": item["totalExercicioAnterior"] if item["totalExercicioAnterior"] else "",
            "Bens - Exercicio Atual": item["totalExercicioAtual"] if item["totalExercicioAtual"] else "",
            "Dividas - Exercicio Anterior": item["dividasOnusReaisExercicioAnterior"] if item["dividasOnusReaisExercicioAnterior"] else "",
            "Dividas - Exercicio Atual": item["dividasOnusReaisExercicioAtual"] if item["dividasOnusReaisExercicioAtual"] else "",
            "Saldo Imposto a Pagar": item["saldoImpostoPagar"] if item["saldoImpostoPagar"] else ""
        })
        
    df_saida = pd.DataFrame(lista_para_df)
    
    # Salva na mesma pasta do config
    pasta_destino = os.path.dirname(ARQ_PLANILHA_FINAL)
    nome_planilha_saida = os.path.join(pasta_destino, "clientes_transmitidos_detalhes.xlsx")
    
    try:
        df_saida.to_excel(nome_planilha_saida, index=False)
        print(f"\nBusca concluída! Resultados salvos em:")
        print(f"  - Planilha: {nome_planilha_saida}")
            
        # Exibe uma amostra
        print("\nAmostra dos resultados:")
        print(df_saida.head())
    except Exception as e:
        print(f"[ERRO] Falha ao salvar a planilha de saída: {e}")

if __name__ == "__main__":
    main()
