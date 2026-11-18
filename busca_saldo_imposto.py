# busca_saldo_imposto.py
import os
import re
import xml.etree.ElementTree as ET
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import (
    ARQ_COMPUTADORES,
    PASTA_BASE_RFB,
    ANO_IRPF,
    SUBPASTA_DADOS
)
from utils import (
    escrever_log,
    limpar_cpf,
    formatar_cpf
)


def ler_computadores():
    try:
        df = pd.read_excel(ARQ_COMPUTADORES)
        return df
    except Exception as e:
        print(f"[ERRO] Ler planilha de computadores: {e}")
        return None


def montar_caminho_base(computador):
    return rf"\\{computador}\C$\{PASTA_BASE_RFB}\IRPF{ANO_IRPF}"


def extrair_cpf_correto_do_xml(caminho_xml, pasta_cpf):
    """
    Extrai o CPF do contribuinte titular de forma estruturada.
    """
    try:
        tree = ET.parse(caminho_xml)
        root = tree.getroot()
        ns = {"ns": "http://www.receita.fazenda.gov.br/declaracao"}
        copia_id = root.find("ns:copiaIdentificador", ns)
        if copia_id is not None:
            cpf_xml = copia_id.get("cpf")
            if cpf_xml:
                return limpar_cpf(cpf_xml)
    except Exception:
        pass

    # Fallback para o nome da pasta se for um CPF válido
    cpf_pasta = limpar_cpf(pasta_cpf)
    if len(cpf_pasta) == 11 and cpf_pasta.isdigit():
        return cpf_pasta

    # Fallback final via regex
    try:
        with open(caminho_xml, "r", encoding="latin-1") as f:
            conteudo = f.read()
        match = re.search(r'cpf="([\d\.\-]+)"', conteudo)
        if match:
            return limpar_cpf(match.group(1))
    except Exception:
        pass

    return None


def extrair_saldo_do_xml(caminho_xml):
    """
    Busca o atributo ou tag 'saldoImpostoPagar' no XML da declaração de forma robusta.
    """
    try:
        tree = ET.parse(caminho_xml)
        root = tree.getroot()
        
        # Percorre recursivamente todos os elementos do XML
        for elem in root.iter():
            # 1. Verifica nos atributos do elemento
            for attr_name, attr_val in elem.attrib.items():
                if attr_name.lower() == "saldoimpostopagar":
                    return attr_val.strip()
            
            # 2. Verifica se a tag termina com saldoImpostoPagar
            tag_local = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            if tag_local.lower() == "saldoimpostopagar" and elem.text:
                return elem.text.strip()
                
    except Exception as e:
        # Fallback para regex caso ocorra erro no parse XML
        try:
            with open(caminho_xml, "r", encoding="latin-1") as f:
                conteudo = f.read()
            match_attr = re.search(r'saldoImpostoPagar\s*=\s*["\']([^"\']*)["\']', conteudo, re.IGNORECASE)
            if match_attr:
                return match_attr.group(1).strip()
        except Exception:
            pass
            
    return None


def processar_maquina_para_saldo(nome_usuario, computador, caminho_custom=None):
    resultados = {}

    if caminho_custom:
        caminho_base = caminho_custom
    else:
        caminho_base = montar_caminho_base(computador)

    pasta_dados = os.path.join(caminho_base, SUBPASTA_DADOS)

    try:
        if os.path.exists(pasta_dados):
            for pasta_cpf in os.listdir(pasta_dados):
                caminho_pasta = os.path.join(pasta_dados, pasta_cpf)
                if not os.path.isdir(caminho_pasta):
                    continue

                xmls_na_pasta = [arq for arq in os.listdir(caminho_pasta) if arq.lower().endswith(".xml")]
                if not xmls_na_pasta:
                    continue

                # Identifica qual XML é a declaração (e não recibo ou metadados)
                xml_escolhido = None
                for arq in xmls_na_pasta:
                    caminho_xml = os.path.join(caminho_pasta, arq)
                    try:
                        tree = ET.parse(caminho_xml)
                        root = tree.getroot()
                        if "DeclaracaoIRPF" in root.get("classeJava", ""):
                            xml_escolhido = caminho_xml
                            break
                    except Exception:
                        pass

                # Se não achou com classeJava, usa o primeiro xml
                if not xml_escolhido:
                    xml_escolhido = os.path.join(caminho_pasta, xmls_na_pasta[0])

                cpf = extrair_cpf_correto_do_xml(xml_escolhido, pasta_cpf)
                saldo = extrair_saldo_do_xml(xml_escolhido)

                if cpf:
                    cpf_limpo = limpar_cpf(cpf)
                    if saldo is not None:
                        resultados[cpf_limpo] = saldo

    except Exception as e:
        print(f"[ERRO MAQUINA] {computador or 'CUSTOM'}: {e}")

    return resultados


def main():
    print("=== INICIANDO BUSCA DE SALDO A PAGAR NOS XMLS ===")
    df = ler_computadores()
    if df is None:
        print("[ERRO] Não foi possível ler a planilha de computadores.")
        return

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

    todos_saldos = {}

    print(f"Varrendo {len(maquinas)} computadores/caminhos...")
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [
            executor.submit(processar_maquina_para_saldo, n, pc, caminho)
            for n, pc, caminho in maquinas
        ]

        for future in as_completed(futures):
            resultado = future.result()
            todos_saldos.update(resultado)

    # Armazena em um arquivo formatado: CPF | valor do campo
    nome_arquivo_saida = r"H:\TI - INFORMATICA\Publico\IRPF2026\monitor_irpf\rendimentos_totais2.txt"
    nome_planilha_saida = r"H:\TI - INFORMATICA\Publico\IRPF2026\monitor_irpf\rendimentos_totais2.xlsx"
    try:
        # Salva no arquivo de texto
        with open(nome_arquivo_saida, "w", encoding="utf-8") as f:
            f.write("cpf | valor do campo\n")
            for cpf_limpo, valor in sorted(todos_saldos.items()):
                cpf_formatado = formatar_cpf(cpf_limpo)
                f.write(f"{cpf_formatado} | {valor}\n")
        
        # Salva na nova planilha Excel
        lista_dados = []
        for cpf_limpo, valor in sorted(todos_saldos.items()):
            lista_dados.append({
                "CPF": formatar_cpf(cpf_limpo),
                "Valor do Campo": valor
            })
        df_saida = pd.DataFrame(lista_dados)
        df_saida.to_excel(nome_planilha_saida, index=False)

        print(f"\nBusca concluída! Resultados salvos em:")
        print(f"  - Texto: {os.path.abspath(nome_arquivo_saida)}")
        print(f"  - Planilha: {os.path.abspath(nome_planilha_saida)}")
        print(f"Total de registros encontrados: {len(todos_saldos)}")
        
        # Exibe uma amostra na tela
        print("\nAmostra dos resultados:")
        for cpf_limpo, valor in list(sorted(todos_saldos.items()))[:10]:
            print(f"{formatar_cpf(cpf_limpo)} | {valor}")
            
    except Exception as e:
        print(f"[ERRO ESCREVER RESULTADOS] {e}")


if __name__ == "__main__":
    main()
