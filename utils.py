import os
from datetime import datetime
import re
import xml.etree.ElementTree as ET
import threading
from config import PASTA_LOGS

log_lock = threading.Lock()

def formatar_cpf(cpf):
    cpf = limpar_cpf(cpf)

    if len(cpf) != 11:
        return cpf  # retorna como está se inválido

    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def garantir_pasta_logs():
    if not os.path.exists(PASTA_LOGS):
        os.makedirs(PASTA_LOGS)
        

def escrever_log_por_usuario(usuario, mensagem):
    garantir_pasta_logs()

    pasta_usuario = os.path.join(PASTA_LOGS, usuario)

    if not os.path.exists(pasta_usuario):
        os.makedirs(pasta_usuario)

    arquivo = os.path.join(
        pasta_usuario,
        f"log_{datetime.now().strftime('%Y-%m-%d')}.txt"
    )

    with log_lock:
        with open(arquivo, "a", encoding="utf-8") as f:
            f.write(f"{mensagem}\n")


def limpar_cpf(cpf):
    if not cpf:
        return ""
    return "".join(filter(str.isdigit, str(cpf)))


def escrever_log(mensagem):
    garantir_pasta_logs()

    arquivo = os.path.join(
        PASTA_LOGS,
        f"log_{datetime.now().strftime('%Y-%m-%d')}.txt"
    )

    with log_lock:
        with open(arquivo, "a", encoding="utf-8") as f:
            f.write(f"{mensagem}\n")


def extrair_cpf_do_xml(caminho_xml, pasta_cpf=None):
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

    # Fallback para o nome da pasta se fornecido e for um CPF válido
    if pasta_cpf:
        cpf_pasta = limpar_cpf(pasta_cpf)
        if len(cpf_pasta) == 11 and cpf_pasta.isdigit():
            return cpf_pasta

    # Fallback para regex
    try:
        with open(caminho_xml, "r", encoding="latin-1") as f:
            conteudo = f.read()

        match = re.search(r'cpf="([\d\.\-]+)"', conteudo)

        if match:
            return limpar_cpf(match.group(1))

    except Exception as e:
        escrever_log(f"[ERRO XML] {caminho_xml} -> {e}")

    return None


# 🔥 NOVO
def extrair_nome_do_xml(caminho_xml):
    try:
        tree = ET.parse(caminho_xml)
        root = tree.getroot()

        ns = {"ns": "http://www.receita.fazenda.gov.br/declaracao"}
        copia_id = root.find("ns:copiaIdentificador", ns)

        if copia_id is not None:
            return copia_id.get("nome")

    except Exception as e:
        escrever_log(f"[ERRO XML NOME] {caminho_xml} -> {e}")

    return None
