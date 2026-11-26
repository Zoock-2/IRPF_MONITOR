# busca_rendimentos_irpf.py

import os
import re
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import (RENDIMENTOS_SAIDAS, ARQUIVO_EXCEL_SAIDA, ARQUIVO_TEXTO_SAIDA)
import pandas as pd

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


PASTA_SAIDA = RENDIMENTOS_SAIDAS

ARQUIVO_EXCEL_SAIDA = os.path.join(
    PASTA_SAIDA,ARQUIVO_EXCEL_SAIDA
    
)

ARQUIVO_TEXTO_SAIDA = os.path.join(
    PASTA_SAIDA,
    ARQUIVO_TEXTO_SAIDA
)


def ler_computadores():
    """
    Lê a planilha contendo os computadores e caminhos que serão
    pesquisados.
    """
    try:
        df = pd.read_excel(
            ARQ_COMPUTADORES,
            engine="openpyxl"
        )

        return df

    except Exception as e:
        print(f"[ERRO] Ler planilha de computadores: {e}")
        return None


def montar_caminho_base(computador):
    """
    Monta o caminho de rede padrão para o computador.
    """
    return rf"\\{computador}\C$\{PASTA_BASE_RFB}\IRPF{ANO_IRPF}"


def obter_nome_local_tag(tag):
    """
    Remove o namespace de uma tag XML.

    Exemplo:
    {http://www.receita.fazenda.gov.br/declaracao}resumo

    Retorna:
    resumo
    """
    if not tag:
        return ""

    if "}" in tag:
        return tag.split("}", 1)[1]

    return tag


def converter_valor_brasileiro(valor):
    """
    Converte um valor no formato brasileiro para Decimal.

    Exemplos:
    1.844.244,19 -> Decimal("1844244.19")
    70.036,67    -> Decimal("70036.67")
    0,00         -> Decimal("0.00")

    O Excel receberá o valor como número, não como texto.
    """
    if valor is None:
        return None

    valor = str(valor).strip()

    if valor == "":
        return None

    valor = valor.replace("R$", "")
    valor = valor.replace(" ", "")
    valor = valor.replace(".", "")
    valor = valor.replace(",", ".")

    try:
        return Decimal(valor)

    except InvalidOperation:
        return None


def formatar_valor_brasileiro(valor):
    """
    Formata um número no padrão brasileiro para o arquivo TXT.
    """
    if valor is None:
        return ""

    try:
        valor_decimal = Decimal(str(valor))

        valor_formatado = f"{valor_decimal:,.2f}"

        return (
            valor_formatado
            .replace(",", "#")
            .replace(".", ",")
            .replace("#", ".")
        )

    except Exception:
        return str(valor)


def extrair_cpf_correto_do_xml(caminho_xml, pasta_cpf):
    """
    Extrai o CPF do titular.

    Ordem de tentativa:

    1. copiaIdentificador
    2. identificadorDeclaracao
    3. identificadorDec
    4. nome da pasta
    5. expressão regular
    """
    try:
        tree = ET.parse(caminho_xml)
        root = tree.getroot()

        tags_identificacao = {
            "copiaidentificador",
            "identificadordeclaracao",
            "identificadordec"
        }

        for elem in root.iter():
            tag_local = obter_nome_local_tag(elem.tag).lower()

            if tag_local in tags_identificacao:
                cpf_xml = elem.get("cpf")

                if cpf_xml:
                    cpf_limpo = limpar_cpf(cpf_xml)

                    if len(cpf_limpo) == 11 and cpf_limpo.isdigit():
                        return cpf_limpo

    except Exception as e:
        escrever_log(
            f"[AVISO CPF XML] Não foi possível extrair o CPF "
            f"estruturado de {caminho_xml}: {e}"
        )

    # Primeiro fallback: nome da pasta
    cpf_pasta = limpar_cpf(pasta_cpf)

    if len(cpf_pasta) == 11 and cpf_pasta.isdigit():
        return cpf_pasta

    # Segundo fallback: expressão regular
    try:
        with open(
            caminho_xml,
            "r",
            encoding="latin-1",
            errors="ignore"
        ) as arquivo:

            conteudo = arquivo.read()

        matches = re.findall(
            r'\bcpf\s*=\s*[\d.\-]+["\']',
            conteudo,
            re.IGNORECASE
        )

        for cpf_encontrado in matches:
            cpf_limpo = limpar_cpf(cpf_encontrado)

            if len(cpf_limpo) == 11 and cpf_limpo.isdigit():
                return cpf_limpo

    except Exception as e:
        escrever_log(
            f"[AVISO CPF REGEX] Não foi possível pesquisar CPF "
            f"em {caminho_xml}: {e}"
        )

    return None


def extrair_nome_contribuinte(caminho_xml):
    """
    Extrai o nome do titular do XML.
    """
    try:
        tree = ET.parse(caminho_xml)
        root = tree.getroot()

        tags_identificacao = {
            "copiaidentificador",
            "identificadordeclaracao",
            "identificadordec"
        }

        for elem in root.iter():
            tag_local = obter_nome_local_tag(elem.tag).lower()

            if tag_local in tags_identificacao:
                nome = elem.get("nome")

                if nome:
                    return nome.strip()

    except Exception:
        pass

    return ""


def extrair_informacoes_rendimentos(caminho_xml):
    """
    Extrai do XML os seguintes campos:

    rendIsentosNaoTributaveis
    rendIsentosTributacaoExclusiva
    totalRendimentos

    Os dois primeiros ficam normalmente em:

    resumo/outrasInformacoes

    O totalRendimentos fica normalmente em:

    resumo/rendimentosTributaveisDeducoes
    """
    informacoes = {
        "rendIsentosNaoTributaveis": None,
        "rendIsentosTributacaoExclusiva": None,
        "totalRendimentos": None
    }

    try:
        tree = ET.parse(caminho_xml)
        root = tree.getroot()

        for elem in root.iter():
            tag_local = obter_nome_local_tag(elem.tag).lower()

            if tag_local == "outrasinformacoes":
                valor_isentos = elem.get(
                    "rendIsentosNaoTributaveis"
                )

                valor_exclusiva = elem.get(
                    "rendIsentosTributacaoExclusiva"
                )

                if valor_isentos is not None:
                    informacoes[
                        "rendIsentosNaoTributaveis"
                    ] = converter_valor_brasileiro(valor_isentos)

                if valor_exclusiva is not None:
                    informacoes[
                        "rendIsentosTributacaoExclusiva"
                    ] = converter_valor_brasileiro(valor_exclusiva)

            elif tag_local == "rendimentostributaveisdeducoes":
                valor_total = elem.get("totalRendimentos")

                if valor_total is not None:
                    informacoes[
                        "totalRendimentos"
                    ] = converter_valor_brasileiro(valor_total)

        # Se encontrou pelo menos um valor, retorna o resultado
        if any(
            valor is not None
            for valor in informacoes.values()
        ):
            return informacoes

    except Exception as e:
        escrever_log(
            f"[ERRO XML] Não foi possível processar "
            f"{caminho_xml}: {e}"
        )

    # Fallback usando expressão regular
    try:
        with open(
            caminho_xml,
            "r",
            encoding="latin-1",
            errors="ignore"
        ) as arquivo:

            conteudo = arquivo.read()

        campos = [
            "rendIsentosNaoTributaveis",
            "rendIsentosTributacaoExclusiva",
            "totalRendimentos"
        ]

        for campo in campos:
            if informacoes[campo] is not None:
                continue

            match = re.search(
                rf'{campo}\s*=\s*[^"\']*["\']',
                conteudo,
                re.IGNORECASE
            )

            if match:
                informacoes[campo] = converter_valor_brasileiro(
                    match.group(1)
                )

    except Exception as e:
        escrever_log(
            f"[ERRO FALLBACK] Não foi possível pesquisar os "
            f"rendimentos em {caminho_xml}: {e}"
        )

    return informacoes


def localizar_xml_declaracao(caminho_pasta):
    """
    Localiza o XML principal da declaração IRPF.

    Prioridade:

    1. XML com classeJava contendo DeclaracaoIRPF
    2. XML contendo a tag resumo
    3. Primeiro XML encontrado
    """
    try:
        xmls_na_pasta = [
            arquivo
            for arquivo in os.listdir(caminho_pasta)
            if arquivo.lower().endswith(".xml")
        ]

    except Exception:
        return None

    if not xmls_na_pasta:
        return None

    # Primeira tentativa: classeJava
    for arquivo in xmls_na_pasta:
        caminho_xml = os.path.join(
            caminho_pasta,
            arquivo
        )

        try:
            tree = ET.parse(caminho_xml)
            root = tree.getroot()

            classe_java = root.get("classeJava", "")

            if "DeclaracaoIRPF" in classe_java:
                return caminho_xml

        except Exception:
            continue

    # Segunda tentativa: XML contendo a tag resumo
    for arquivo in xmls_na_pasta:
        caminho_xml = os.path.join(
            caminho_pasta,
            arquivo
        )

        try:
            tree = ET.parse(caminho_xml)
            root = tree.getroot()

            for elem in root.iter():
                tag_local = obter_nome_local_tag(
                    elem.tag
                ).lower()

                if tag_local == "resumo":
                    return caminho_xml

        except Exception:
            continue

    # Fallback: primeiro XML encontrado
    return os.path.join(
        caminho_pasta,
        xmls_na_pasta[0]
    )


def processar_maquina(
    nome_usuario,
    computador,
    caminho_custom=None
):
    """
    Processa todas as pastas de CPF encontradas no computador
    ou no caminho personalizado.
    """
    resultados = []

    if caminho_custom:
        caminho_base = caminho_custom
    else:
        caminho_base = montar_caminho_base(computador)

    pasta_dados = os.path.join(
        caminho_base,
        SUBPASTA_DADOS
    )

    try:
        if not os.path.exists(pasta_dados):
            escrever_log(
                f"[CAMINHO NÃO ENCONTRADO] "
                f"{computador or 'CUSTOM'}: {pasta_dados}"
            )

            return resultados

        for pasta_cpf in os.listdir(pasta_dados):
            caminho_pasta = os.path.join(
                pasta_dados,
                pasta_cpf
            )

            if not os.path.isdir(caminho_pasta):
                continue

            xml_escolhido = localizar_xml_declaracao(
                caminho_pasta
            )

            if not xml_escolhido:
                continue

            cpf = extrair_cpf_correto_do_xml(
                xml_escolhido,
                pasta_cpf
            )

            if not cpf:
                escrever_log(
                    f"[CPF NÃO ENCONTRADO] {xml_escolhido}"
                )
                continue

            nome_contribuinte = extrair_nome_contribuinte(
                xml_escolhido
            )

            rendimentos = extrair_informacoes_rendimentos(
                xml_escolhido
            )

            encontrou_algum_valor = any(
                valor is not None
                for valor in rendimentos.values()
            )

            if not encontrou_algum_valor:
                escrever_log(
                    f"[RENDIMENTOS NÃO ENCONTRADOS] "
                    f"{xml_escolhido}"
                )
                continue

            resultados.append({
                "Nome Planilha": nome_usuario,
                "Nome Contribuinte": nome_contribuinte,
                "CPF": formatar_cpf(cpf),
                "rendIsentosNaoTributaveis": rendimentos[
                    "rendIsentosNaoTributaveis"
                ],
                "rendIsentosTributacaoExclusiva": rendimentos[
                    "rendIsentosTributacaoExclusiva"
                ],
                "totalRendimentos": rendimentos[
                    "totalRendimentos"
                ],
                "Computador": computador,
                "Caminho XML": xml_escolhido
            })

    except Exception as e:
        print(
            f"[ERRO MAQUINA] "
            f"{computador or 'CUSTOM'}: {e}"
        )

        escrever_log(
            f"[ERRO MAQUINA] "
            f"{computador or 'CUSTOM'}: {e}"
        )

    return resultados


def consolidar_resultados(resultados):
    """
    Consolida os resultados e evita duplicidade de CPF.

    Caso o mesmo CPF seja encontrado em mais de um computador,
    mantém o primeiro registro encontrado com valores.
    """
    consolidados = {}

    for registro in resultados:
        cpf = registro.get("CPF")

        if not cpf:
            continue

        if cpf not in consolidados:
            consolidados[cpf] = registro
            continue

        registro_atual = consolidados[cpf]

        campos_valores = [
            "rendIsentosNaoTributaveis",
            "rendIsentosTributacaoExclusiva",
            "totalRendimentos"
        ]

        for campo in campos_valores:
            if (
                registro_atual.get(campo) is None
                and registro.get(campo) is not None
            ):
                registro_atual[campo] = registro[campo]

    return list(consolidados.values())


def salvar_excel(resultados):
    """
    Salva os resultados em uma planilha Excel e aplica formatação
    monetária.
    """
    colunas = [
        "Nome Planilha",
        "Nome Contribuinte",
        "CPF",
        "rendIsentosNaoTributaveis",
        "rendIsentosTributacaoExclusiva",
        "totalRendimentos",
        "Computador",
        "Caminho XML"
    ]

    df_saida = pd.DataFrame(
        resultados,
        columns=colunas
    )

    # Converte Decimal para float para compatibilidade com Excel
    colunas_valores = [
        "rendIsentosNaoTributaveis",
        "rendIsentosTributacaoExclusiva",
        "totalRendimentos"
    ]

    for coluna in colunas_valores:
        df_saida[coluna] = df_saida[coluna].apply(
            lambda valor: (
                float(valor)
                if valor is not None
                else None
            )
        )

    df_saida = df_saida.sort_values(
        by=[
            "Nome Contribuinte",
            "CPF"
        ],
        na_position="last"
    )

    os.makedirs(
        PASTA_SAIDA,
        exist_ok=True
    )

    with pd.ExcelWriter(
        ARQUIVO_EXCEL_SAIDA,
        engine="openpyxl"
    ) as writer:

        df_saida.to_excel(
            writer,
            sheet_name="Rendimentos",
            index=False
        )

        worksheet = writer.sheets["Rendimentos"]

        # Congela o cabeçalho
        worksheet.freeze_panes = "A2"

        # Ativa o filtro automático
        worksheet.auto_filter.ref = worksheet.dimensions

        # Formatação monetária das colunas D, E e F
        for coluna_excel in ["D", "E", "F"]:
            for celula in worksheet[coluna_excel][1:]:
                celula.number_format = '#,##0.00'

        # Larguras das colunas
        larguras = {
            "A": 25,
            "B": 35,
            "C": 16,
            "D": 30,
            "E": 34,
            "F": 22,
            "G": 20,
            "H": 80
        }

        for coluna, largura in larguras.items():
            worksheet.column_dimensions[coluna].width = largura

    return len(df_saida)


def salvar_txt(resultados):
    """
    Salva uma cópia simplificada em arquivo TXT.
    """
    os.makedirs(
        PASTA_SAIDA,
        exist_ok=True
    )

    with open(
        ARQUIVO_TEXTO_SAIDA,
        "w",
        encoding="utf-8"
    ) as arquivo:

        arquivo.write(
            "CPF | "
            "rendIsentosNaoTributaveis | "
            "rendIsentosTributacaoExclusiva | "
            "totalRendimentos\n"
        )

        for registro in sorted(
            resultados,
            key=lambda item: item.get("CPF", "")
        ):
            arquivo.write(
                f'{registro.get("CPF", "")} | '
                f'{formatar_valor_brasileiro(registro.get("rendIsentosNaoTributaveis"))} | '
                f'{formatar_valor_brasileiro(registro.get("rendIsentosTributacaoExclusiva"))} | '
                f'{formatar_valor_brasileiro(registro.get("totalRendimentos"))}\n'
            )


def main():
    print(
        "=== INICIANDO BUSCA DOS RENDIMENTOS NOS XMLS ==="
    )

    df = ler_computadores()

    if df is None:
        print(
            "[ERRO] Não foi possível ler a planilha "
            "de computadores."
        )
        return

    if "Nome" not in df.columns:
        print(
            "[ERRO] A planilha precisa conter a coluna 'Nome'."
        )
        return

    maquinas = []

    for _, row in df.iterrows():
        nome = str(row["Nome"]).strip()

        computador = ""

        if (
            "Computador" in df.columns
            and pd.notna(row["Computador"])
        ):
            computador = str(
                row["Computador"]
            ).strip()

        caminho_custom = ""

        if (
            "Caminho" in df.columns
            and pd.notna(row["Caminho"])
        ):
            caminho_custom = str(
                row["Caminho"]
            ).strip()

        if not computador and not caminho_custom:
            escrever_log(
                f"[LINHA IGNORADA] Nome: {nome}. "
                f"Computador e Caminho não informados."
            )
            continue

        maquinas.append(
            (
                nome,
                computador,
                caminho_custom
            )
        )

    todos_resultados = []

    print(
        f"Varrendo {len(maquinas)} "
        f"computadores/caminhos..."
    )

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [
            executor.submit(
                processar_maquina,
                nome,
                computador,
                caminho
            )
            for nome, computador, caminho in maquinas
        ]

        for future in as_completed(futures):
            try:
                resultado_maquina = future.result()

                todos_resultados.extend(
                    resultado_maquina
                )

            except Exception as e:
                print(f"[ERRO THREAD] {e}")
                escrever_log(f"[ERRO THREAD] {e}")

    resultados_consolidados = consolidar_resultados(
        todos_resultados
    )

    try:
        total_registros = salvar_excel(
            resultados_consolidados
        )

        salvar_txt(
            resultados_consolidados
        )

        print("\nBusca concluída!")

        print(
            f"Planilha: {ARQUIVO_EXCEL_SAIDA}"
        )

        print(
            f"Arquivo TXT: {ARQUIVO_TEXTO_SAIDA}"
        )

        print(
            f"Total de registros encontrados: "
            f"{total_registros}"
        )

        print("\nAmostra dos resultados:")

        for registro in resultados_consolidados[:10]:
            print(
                f'{registro["CPF"]} | '
                f'Isentos: '
                f'{formatar_valor_brasileiro(registro["rendIsentosNaoTributaveis"])} | '
                f'Exclusiva: '
                f'{formatar_valor_brasileiro(registro["rendIsentosTributacaoExclusiva"])} | '
                f'Tributáveis: '
                f'{formatar_valor_brasileiro(registro["totalRendimentos"])}'
            )

    except Exception as e:
        print(
            f"[ERRO ESCREVER RESULTADOS] {e}"
        )

        escrever_log(
            f"[ERRO ESCREVER RESULTADOS] {e}"
        )


if __name__ == "__main__":
    main()
