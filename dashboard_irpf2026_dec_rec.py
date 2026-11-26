# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

import main as main_script
from config import ARQ_PLANILHA_FINAL, CSV

st.set_page_config(
    page_title="IRPF 2026 — Painel de Declarações",
    layout="wide",
    initial_sidebar_state="expanded"
)

st_autorefresh(interval=60000, limit=10000, key="dataframerefresh")

st.markdown("""
<style>
.stApp {
    background-color: #0f172a;
    color: #e2e8f0;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
input, select, textarea {
    background-color: #1e293b !important;
    color: #e2e8f0 !important;
    border: 1px solid #334155 !important;
}
.dashboard-header {
    background: linear-gradient(135deg, #1e3a5f 0%, #1a2e4a 100%);
    padding: 28px 40px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 2px solid #2563eb;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    border-radius: 16px;
    margin-bottom: 30px;
}
.header-left { display: flex; align-items: center; gap: 16px; }
.header-icon {
    width: 52px; height: 52px;
    background: linear-gradient(135deg, #2563eb, #3b82f6);
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 26px;
}
.dashboard-header h1 { font-size: 1.6rem; font-weight: 700; color: #f1f5f9; margin: 0; }
.dashboard-header p { font-size: 0.85rem; color: #94a3b8; margin: 2px 0 0 0; }
.badge-ano {
    background: #2563eb; color: white;
    padding: 6px 18px; border-radius: 999px;
    font-size: 0.9rem; font-weight: 700; letter-spacing: 1px;
}
.summary-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 16px;
    margin-bottom: 25px;
}
.card {
    border-radius: 16px; padding: 22px 24px;
    position: relative; overflow: hidden;
    color: white;
}
.card::before {
    content: ''; position: absolute;
    top: -30px; right: -30px;
    width: 100px; height: 100px;
    border-radius: 50%; opacity: 0.12; background: white;
}
.card-total { background: linear-gradient(135deg, #1d4ed8, #2563eb); }
.card-andamento { background: linear-gradient(135deg, #b45309, #d97706); }
.card-transmit { background: linear-gradient(135deg, #065f46, #059669); }
.card-resp { background: linear-gradient(135deg, #4c1d95, #7c3aed); }
.card-prazo { background: linear-gradient(135deg, #991b1b, #dc2626); }
.card-label { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 1px; opacity: 0.85; font-weight: 600; }
.card-value { font-size: 2.2rem; font-weight: 800; margin: 6px 0 4px; line-height: 1; }
.card-sub { font-size: 0.8rem; opacity: 0.75; }
.card-icon { font-size: 2.2rem; position: absolute; top: 18px; right: 22px; opacity: 0.4; }
@media (max-width: 1400px) { .summary-grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 900px) { .summary-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 600px) { .summary-grid { grid-template-columns: 1fr; } }
.progress-card {
    background: #1e293b; border-radius: 16px;
    padding: 22px 24px; margin-bottom: 30px;
    border: 1px solid #334155;
}
.progress-label { font-size: 0.82rem; color: #94a3b8; margin-bottom: 10px; }
.progress-bar-bg {
    background: #334155; border-radius: 999px;
    height: 18px; overflow: hidden; position: relative;
}
.progress-bar-fill {
    height: 100%; border-radius: 999px;
    background: linear-gradient(90deg, #059669, #34d399);
    transition: width 1.5s ease; position: relative;
}
.progress-pct {
    position: absolute; right: 10px; top: 50%;
    transform: translateY(-50%);
    font-size: 0.75rem; font-weight: 700; color: white;
}
.progress-legend { display: flex; gap: 24px; margin-top: 10px; font-size: 0.78rem; }
.leg-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 5px; }
.chart-card { background: #1e293b; border-radius: 16px; padding: 28px; border: 1px solid #334155; }
.section-title { font-size: 1.1rem; font-weight: 700; color: #f1f5f9; margin-bottom: 4px; }
.section-sub { font-size: 0.78rem; color: #64748b; margin-bottom: 22px; }
.bar-row {
    display: grid; grid-template-columns: 155px 1fr 55px;
    align-items: center; gap: 10px; margin-bottom: 12px;
}
.bar-name {
    font-size: 0.8rem; color: #cbd5e1;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-align: right;
}
.bar-track {
    height: 22px; background: #0f172a;
    border-radius: 6px; overflow: hidden; display: flex;
}
.bar-seg-a { height: 100%; background: linear-gradient(90deg, #d97706, #f59e0b); }
.bar-seg-t { height: 100%; background: linear-gradient(90deg, #059669, #10b981); }
.bar-total { font-size: 0.8rem; font-weight: 700; color: #f8fafc; text-align: right; }
.bar-row:hover .bar-name { color: #93c5fd; }
.right-panel { display: flex; flex-direction: column; gap: 22px; }
.legend-box { background: #1e293b; border-radius: 16px; padding: 22px; border: 1px solid #334155; }
.legend-item {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 0; border-bottom: 1px solid #334155; font-size: 0.83rem;
}
.legend-item:last-child { border-bottom: none; }
.legend-color { width: 14px; height: 14px; border-radius: 4px; flex-shrink: 0; }
.legend-count { margin-left: auto; font-weight: 700; font-size: 0.9rem; }
.ranking-box { background: #1e293b; border-radius: 16px; padding: 22px; border: 1px solid #334155; }
.rank-item {
    display: flex; align-items: center; gap: 12px;
    padding: 10px 0; border-bottom: 1px solid #1e3a5f;
}
.rank-item:last-child { border-bottom: none; }
.rank-num {
    width: 28px; height: 28px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.75rem; font-weight: 800; flex-shrink: 0;
}
.rank-1 { background: linear-gradient(135deg, #f59e0b, #fbbf24); color: #1a1a1a; }
.rank-2 { background: linear-gradient(135deg, #94a3b8, #cbd5e1); color: #1a1a1a; }
.rank-3 { background: linear-gradient(135deg, #b45309, #d97706); color: white; }
.rank-4 { background: #334155; color: #94a3b8; }
.rank-name { font-size: 0.83rem; color: #e2e8f0; flex: 1; }
.rank-total { font-size: 0.88rem; font-weight: 700; color: #f8fafc; }
.dashboard-footer {
    text-align: center; padding: 18px 40px;
    font-size: 0.75rem; color: #475569;
    border-top: 1px solid #1e293b;
    margin-top: 40px;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=10)
def carregar_dados():
    if os.path.exists(ARQ_PLANILHA_FINAL):
        try:
            return pd.read_excel(ARQ_PLANILHA_FINAL, dtype=str)
        except Exception as e:
            st.warning(f"Aviso: Erro ao ler planilha oficial ({e}). Tentando arquivo local...")

    if os.path.exists("catalogo_irpf2026.xlsx"):
        try:
            return pd.read_excel("catalogo_irpf2026.xlsx", dtype=str)
        except:
            pass

    if os.path.exists(CSV):
        try:
            return pd.read_csv(CSV, dtype=str)
        except:
            pass

    if os.path.exists("catalogo_irpf2026.csv"):
        try:
            return pd.read_csv("catalogo_irpf2026.csv", dtype=str)
        except:
            pass

    return pd.DataFrame(columns=["CPF", "Nome", "Status", "Feita por", "Transmitida por", "Data Transmissão"])

df_original = carregar_dados()

colunas_obrigatorias = ["CPF", "Nome", "Status", "Feita por", "Transmitida por", "Data Transmissão"]
for col in colunas_obrigatorias:
    if col not in df_original.columns:
        if col == "Nome" and "Nome do Cliente" in df_original.columns:
            df_original["Nome"] = df_original["Nome do Cliente"]
        elif col == "Data Transmissão" and "Data Transmisso" in df_original.columns:
            df_original["Data Transmissão"] = df_original["Data Transmisso"]
        else:
            df_original[col] = ""

df_original["Nome"] = df_original["Nome"].fillna("Não Informado").str.strip()
df_original["Status"] = df_original["Status"].fillna("Sem status definido").str.strip()
df_original["Feita por"] = df_original["Feita por"].fillna("").str.strip()
df_original["Transmitida por"] = df_original["Transmitida por"].fillna("").str.strip()
df_original["Data Transmissão"] = df_original["Data Transmissão"].fillna("").str.strip()

lista_responsaveis = set()
for col in ["Feita por", "Transmitida por"]:
    for celula in df_original[col]:
        partes = [p.strip() for p in celula.split(";") if p.strip()]
        for p in partes:
            if p.lower() != "nan":
                lista_responsaveis.add(p)
lista_responsaveis = sorted(list(lista_responsaveis))

st.sidebar.markdown("<h2 style='text-align: center;'>🛠️ Filtros e Controles</h2>", unsafe_allow_html=True)
st.sidebar.markdown("Use os filtros abaixo para restringir os dados em tempo real.")

filtro_busca = st.sidebar.text_input(
    "Busca Livre (Qualquer termo de Nome ou CPF):",
    value="",
    help="Use para buscar por qualquer parte do nome ou CPF de forma livre."
)

filtro_feita = st.sidebar.multiselect(
    "Preparado por (Feita por):",
    options=lista_responsaveis,
    help="Filtra clientes cujo trabalho foi realizado pelos responsáveis selecionados"
)

filtro_transmitida = st.sidebar.multiselect(
    "Transmitido por (Transmitida por):",
    options=lista_responsaveis,
    help="Filtra clientes cuja transmissão foi realizada pelos responsáveis selecionados"
)

status_disponiveis = sorted(list(df_original["Status"].unique()))
filtro_status = st.sidebar.multiselect("Status da Declaração:", options=status_disponiveis)

datas_validas = df_original[df_original["Data Transmissão"] != ""]
filtro_periodo = None
if not datas_validas.empty:
    try:
        datas_convertidas = pd.to_datetime(
            datas_validas["Data Transmissão"],
            format="%d/%m/%Y %H:%M:%S",
            errors="coerce"
        )
        min_d = datas_convertidas.min().date()
        max_d = datas_convertidas.max().date()
        if min_d and max_d and min_d <= max_d:
            st.sidebar.markdown("---")
            filtro_periodo = st.sidebar.date_input(
                "Período de Transmissão:",
                value=(min_d, max_d),
                min_value=min_d,
                max_value=max_d
            )
    except Exception:
        pass

df_filtrado = df_original.copy()

if filtro_busca:
    query = filtro_busca.lower()
    df_filtrado = df_filtrado[
        df_filtrado["Nome"].str.lower().str.contains(query, na=False) |
        df_filtrado["CPF"].str.contains(query, na=False)
    ]

if filtro_feita:
    mask = df_filtrado["Feita por"].apply(
        lambda x: any(resp in [n.strip() for n in str(x).split(";")] for resp in filtro_feita)
    )
    df_filtrado = df_filtrado[mask]

if filtro_transmitida:
    mask = df_filtrado["Transmitida por"].apply(
        lambda x: any(resp in [n.strip() for n in str(x).split(";")] for resp in filtro_transmitida)
    )
    df_filtrado = df_filtrado[mask]

if filtro_status:
    df_filtrado = df_filtrado[df_filtrado["Status"].isin(filtro_status)]

if filtro_periodo and isinstance(filtro_periodo, tuple) and len(filtro_periodo) == 2:
    start_d, end_d = filtro_periodo

    def filtrar_datas(row_date):
        if not row_date or str(row_date).strip() == "":
            return True
        try:
            dt = datetime.strptime(str(row_date).strip(), "%d/%m/%Y %H:%M:%S").date()
            return start_d <= dt <= end_d
        except:
            return False

    df_filtrado = df_filtrado[df_filtrado["Data Transmissão"].apply(filtrar_datas)]

for col in ["CPF", "Nome", "Status", "Feita por", "Transmitida por", "Data Transmissão"]:
    if col not in df_filtrado.columns:
        df_filtrado = df_filtrado.copy()
        df_filtrado[col] = ""

total_registros = len(df_filtrado)

if total_registros == 0:
    total_em_andamento = 0
    total_transmitidas = 0
    total_conflito_pcs = 0
    total_conflito_duplicada = 0
    total_conflitos = 0
    total_sem_status = 0
    total_declaracoes_ativas = 0
    total_resp_ativos = 0
    pct_andamento = 0.0
    pct_transmitidas = 0.0
    resps_ordenados = []
else:
    total_em_andamento = len(df_filtrado[df_filtrado["Status"] == "Em andamento"])
    total_transmitidas = len(df_filtrado[df_filtrado["Status"] == "Transmitida"])
    total_conflito_pcs = len(df_filtrado[df_filtrado["Status"] == "CONFLITO - Múltiplos PCs"])
    total_conflito_duplicada = len(df_filtrado[df_filtrado["Status"] == "CONFLITO - Transmitida duplicada"])
    total_conflitos = total_conflito_pcs + total_conflito_duplicada

    if "Sem status defined" in df_filtrado["Status"].values:
        total_sem_status = len(df_filtrado[df_filtrado["Status"] == "Sem status defined"])
    else:
        total_sem_status = len(df_filtrado[df_filtrado["Status"] == "Sem status definido"])

    total_declaracoes_ativas = total_registros

    responsaveis_ativos = set()
    for col in ["Feita por", "Transmitida por"]:
        for celula in df_filtrado[col]:
            partes = [p.strip() for p in str(celula).split(";") if p.strip()]
            for p in partes:
                if p.lower() != "nan":
                    responsaveis_ativos.add(p)

    total_resp_ativos = len(responsaveis_ativos)
    pct_andamento = (total_em_andamento / total_declaracoes_ativas * 100)
    pct_transmitidas = (total_transmitidas / total_declaracoes_ativas * 100)

prazo_final = datetime(2026, 5, 29, 23, 59, 0)
agora = datetime.now()

if agora < prazo_final:
    delta = prazo_final - agora
    dias = delta.days
    horas = delta.seconds // 3600
    minutos = (delta.seconds % 3600) // 60
    segundos = delta.seconds % 60

    if dias > 0:
        tempo_restante_str = f"{dias}d {horas}h"
    elif horas > 0:
        tempo_restante_str = f"{horas}h {minutos}m {segundos}s"
    else:
        tempo_restante_str = f"{minutos}m {segundos}s"

    sub_prazo_text = "Prazo: 29/05 às 23:59"
else:
    tempo_restante_str = "Encerrado"
    sub_prazo_text = "Finalizado em 29/05"

dados_responsaveis = {}
if total_registros > 0:
    for idx, row in df_filtrado.iterrows():
        status = row["Status"]
        feitas = [n.strip() for n in str(row["Feita por"]).split(";") if n.strip() and n.strip().lower() != "nan"]
        transm = [n.strip() for n in str(row["Transmitida por"]).split(";") if n.strip() and n.strip().lower() != "nan"]
        uniao = set(feitas + transm)

        for r in uniao:
            if r not in dados_responsaveis:
                dados_responsaveis[r] = {"andamento": 0, "transmitida": 0, "total": 0}

            if status == "Transmitida":
                dados_responsaveis[r]["transmitida"] += 1
            else:
                dados_responsaveis[r]["andamento"] += 1

            dados_responsaveis[r]["total"] += 1

resps_ordenados = sorted(
    dados_responsaveis.items(),
    key=lambda x: x[1]["total"],
    reverse=True
) if dados_responsaveis else []

caminho_planilha = (
    ARQ_PLANILHA_FINAL
    if os.path.exists(ARQ_PLANILHA_FINAL)
    else ("catalogo_irpf2026.xlsx" if os.path.exists("catalogo_irpf2026.xlsx") else "")
)

if caminho_planilha and os.path.exists(caminho_planilha):
    try:
        mtime = os.path.getmtime(caminho_planilha)
        ultima_atualizacao = datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        ultima_atualizacao = "Erro ao ler data"
else:
    ultima_atualizacao = "Não disponível"

st.markdown(f"""
<div class="dashboard-header">
  <div class="header-left">
    <div class="header-icon">📋</div>
    <div>
      <h1>Painel de Declarações IRPF</h1>
      <p>Controle interativo de status por responsável — Fonte de dados: {os.path.basename(ARQ_PLANILHA_FINAL)} &nbsp;·&nbsp; <b>Última atualização:</b> {ultima_atualizacao}</p>
    </div>
  </div>
  <span class="badge-ano">IRPF {datetime.now().year}</span>
</div>
""", unsafe_allow_html=True)

if df_filtrado.empty:
    st.markdown(f"""
    <div style="background: rgba(30, 41, 59, 0.7); border: 2px solid #ef4444; border-radius: 20px; padding: 60px 40px; text-align: center; margin: 40px auto; max-width: 800px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); backdrop-filter: blur(12px);">
      <div style="font-size: 5rem; margin-bottom: 25px;">🔍❌</div>
      <h3 style="color: #f8fafc; font-size: 1.8rem; font-weight: 800; margin: 0 0 15px 0;">Termo não encontrado</h3>
      <div style="width: 60px; height: 4px; background: #ef4444; margin: 0 auto 25px auto; border-radius: 2px;"></div>
      <p style="color: #cbd5e1; font-size: 1.05rem; max-width: 600px; margin: 0 auto 25px auto; line-height: 1.7; font-weight: 500;">
        Não encontramos nenhuma declaração ou cliente que corresponda aos filtros e termos pesquisados na barra lateral.
      </p>
      <div style="background: rgba(15, 23, 42, 0.6); padding: 25px; border-radius: 12px; border: 1px solid #334155; max-width: 580px; margin: 0 auto; text-align: left;">
        <span style="color: #60a5fa; font-weight: 700; font-size: 0.88rem; display: block; text-transform: uppercase; margin-bottom: 10px;">💡 Dicas de Solução:</span>
        <ul style="color: #94a3b8; font-size: 0.92rem; margin: 0; padding-left: 20px; line-height: 1.7;">
          <li style="margin-bottom: 8px;">Verifique se digitou o nome ou CPF corretamente na <b>Busca Livre</b>.</li>
          <li style="margin-bottom: 8px;">Remova ou altere os filtros de <b>Responsável</b> ou <b>Status</b>.</li>
          <li>Certifique-se de que os dados foram carregados da planilha de origem corretamente.</li>
        </ul>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="dashboard-footer">
      Gerado em {datetime.now().strftime("%d/%m/%Y %H:%M:%S")} &nbsp;·&nbsp;
      Fonte: {os.path.basename(ARQ_PLANILHA_FINAL)} &nbsp;·&nbsp;
      0 registros filtrados do catálogo ({len(df_original)} total)
    </div>
    """, unsafe_allow_html=True)
    st.stop()

st.markdown(f"""
<div class="summary-grid">
  <div class="card card-total">
    <div class="card-icon">📊</div>
    <div class="card-label">Total Ativo</div>
    <div class="card-value">{total_declaracoes_ativas}</div>
    <div class="card-sub">Todos os Status</div>
  </div>
  <div class="card card-andamento">
    <div class="card-icon">⏳</div>
    <div class="card-label">Em Andamento</div>
    <div class="card-value">{total_em_andamento}</div>
    <div class="card-sub">{pct_andamento:.1f}% do total ativo</div>
  </div>
  <div class="card card-transmit">
    <div class="card-icon">✅</div>
    <div class="card-label">Transmitidas</div>
    <div class="card-value">{total_transmitidas}</div>
    <div class="card-sub">{pct_transmitidas:.1f}% do total ativo</div>
  </div>
  <div class="card card-resp">
    <div class="card-icon">👥</div>
    <div class="card-label">Responsáveis</div>
    <div class="card-value">{total_resp_ativos}</div>
    <div class="card-sub">Com declarações ativas</div>
  </div>
  <div class="card card-prazo">
    <div class="card-icon">⏱️</div>
    <div class="card-label">Tempo Restante</div>
    <div class="card-value" id="countdown-timer">{tempo_restante_str}</div>
    <div class="card-sub" id="countdown-sub">{sub_prazo_text}</div>
  </div>
</div>
""", unsafe_allow_html=True)

pct_geral_transmissao = (total_transmitidas / total_registros * 100) if total_registros > 0 else 0.0
st.markdown(f"""
<div class="progress-card">
  <div class="progress-label">Progresso geral de transmissão</div>
  <div class="progress-bar-bg">
    <div class="progress-bar-fill" style="width: {pct_geral_transmissao:.1f}%">
      <span class="progress-pct">{pct_geral_transmissao:.1f}%</span>
    </div>
  </div>
  <div class="progress-legend">
    <span><span class="leg-dot" style="background:#34d399"></span>Transmitidas: {total_transmitidas}</span>
    <span><span class="leg-dot" style="background:#f59e0b"></span>Em Andamento/Outros: {total_registros - total_transmitidas}</span>
    <span><span class="leg-dot" style="background:#ff0000"></span>CONFLITO — Múltiplos PCs: {total_conflito_pcs}</span>
    <span><span class="leg-dot" style="background:#334155"></span>Total catálogo filtrado: {total_registros}</span>
  </div>
</div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([1.7, 1.0])

with col_left:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📈 Declarações por Responsável</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">🟡 Em Andamento &nbsp;|&nbsp; 🟢 Transmitidas &nbsp;· Passe o mouse sobre as barras no navegador para detalhes</div>', unsafe_allow_html=True)

    if resps_ordenados:
        max_valor_grafico = max([v["total"] for k, v in resps_ordenados])
        barras_html = ""

        for nome, counts in resps_ordenados:
            total = counts["total"]
            andamento = counts["andamento"]
            transmitida = counts["transmitida"]

            w_andamento = (andamento / max_valor_grafico) * 100
            w_transmitida = (transmitida / max_valor_grafico) * 100
            pct_concluida = int((transmitida / total) * 100) if total > 0 else 0

            barras_html += f"""
            <div class="bar-row" title="{nome}&#10;⏳ Em andamento: {andamento}&#10;✅ Transmitidas: {transmitida}&#10;📊 Total: {total} ({pct_concluida}% transmitidas)">
              <div class="bar-name" title="{nome}">{nome}</div>
              <div class="bar-track">
                <div class="bar-seg-a" style="width: {w_andamento:.2f}%"></div>
                <div class="bar-seg-t" style="width: {w_transmitida:.2f}%"></div>
              </div>
              <div class="bar-total">{total} ({pct_concluida}%)</div>
            </div>
            """

        st.markdown(barras_html, unsafe_allow_html=True)
    else:
        st.info("Nenhum dado de responsável atende aos filtros atuais.")

    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="right-panel">', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="legend-box">
      <div class="section-title" style="margin-bottom:14px">🎨 Legenda de Status</div>
      <div class="legend-item">
        <span class="legend-color" style="background:#f59e0b"></span>
        <span>Em Andamento</span>
        <span class="legend-count" style="color:#fbbf24">{total_em_andamento}</span>
      </div>
      <div class="legend-item">
        <span class="legend-color" style="background:#10b981"></span>
        <span>Transmitidas</span>
        <span class="legend-count" style="color:#34d399">{total_transmitidas}</span>
      </div>
      <div class="legend-item">
        <span class="legend-color" style="background:#ef4444"></span>
        <span>CONFLITO — Múltiplos PCs</span>
        <span class="legend-count" style="color:#fca5a5">{total_conflito_pcs}</span>
      </div>
      <div class="legend-item">
        <span class="legend-color" style="background:#dc2626"></span>
        <span>CONFLITO — Transmitida duplicada</span>
        <span class="legend-count" style="color:#fca5a5">{total_conflito_duplicada}</span>
      </div>
      <div class="legend-item">
        <span class="legend-color" style="background:#475569"></span>
        <span>Sem status definido</span>
        <span class="legend-count" style="color:#94a3b8">{total_sem_status}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="ranking-box">', unsafe_allow_html=True)
    st.markdown('<div class="section-title" style="margin-bottom:4px">🏆 Top 5 Responsáveis</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Por volume total de declarações</div>', unsafe_allow_html=True)

    top5 = resps_ordenados[:5]
    if top5:
        ranking_html = ""

        for i, (nome, counts) in enumerate(top5):
            pos = i + 1
            classe_rank = f"rank-{pos}" if pos <= 3 else "rank-4"

            ranking_html += f"""
            <div class="rank-item">
              <div class="rank-num {classe_rank}">{pos}</div>
              <div class="rank-name">{nome}</div>
              <div style="font-size:0.75rem;color:#94a3b8;white-space:nowrap;margin-right:10px;">
                {counts['andamento']}⏳ &nbsp;{counts['transmitida']}✅
              </div>
              <div class="rank-total">{counts['total']}</div>
            </div>
            """

        st.markdown(ranking_html, unsafe_allow_html=True)
    else:
        st.info("Nenhum ranking disponível com os filtros atuais.")

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br><hr style='border-color: #1e293b;'><br>", unsafe_allow_html=True)
st.markdown("A tabela abaixo permite visualizar os dados e baixar o arquivo DEC e o recibo REC de cada cliente.")

df_table = df_filtrado.copy().reset_index(drop=True)
total_linhas = len(df_table)

if total_linhas == 0:
    st.info("Nenhum registro encontrado para exibir na tabela.")
else:
    ITENS_POR_PAGINA = 50
    total_paginas = (total_linhas - 1) // ITENS_POR_PAGINA + 1

    if total_paginas > 1:
        pagina_atual = st.number_input(
            f"Página (1 a {total_paginas}) - Total de {total_linhas} registros:",
            min_value=1,
            max_value=total_paginas,
            value=1
        )
    else:
        pagina_atual = 1
        st.markdown(
            f"<span style='color: #94a3b8; font-size: 0.85rem;'>Total de {total_linhas} registros exibidos.</span>",
            unsafe_allow_html=True
        )

    inicio_idx = (pagina_atual - 1) * ITENS_POR_PAGINA
    fim_idx = inicio_idx + ITENS_POR_PAGINA
    df_pagina = df_table.iloc[inicio_idx:fim_idx]

    st.markdown(
        "<div style='background-color: #1e293b; padding: 10px; border-radius: 8px 8px 0 0; border: 1px solid #334155; margin-top: 15px;'>",
        unsafe_allow_html=True
    )

    h_cols = st.columns([1.5, 3, 2, 2, 2, 1.5])
    h_cols[0].markdown("**CPF**")
    h_cols[1].markdown("**Cliente**")
    h_cols[2].markdown("**Status**")
    h_cols[3].markdown("**Transmitido por**")
    h_cols[4].markdown("**Data**")
    h_cols[5].markdown("**Ação**")
    st.markdown("</div>", unsafe_allow_html=True)

    import io
    import zipfile
    from config import DOCS

    st.markdown(
        "<div style='border-left: 1px solid #334155; border-right: 1px solid #334155; border-bottom: 1px solid #334155; padding: 10px; border-radius: 0 0 8px 8px;'>",
        unsafe_allow_html=True
    )

    for idx, row in df_pagina.iterrows():
        cpf = str(row["CPF"]).strip()
        nome = str(row["Nome"]).strip()

        r_cols = st.columns([1.5, 3, 2, 2, 2, 1.5])
        r_cols[0].write(cpf)
        r_cols[1].write(nome)
        r_cols[2].write(str(row["Status"]).strip())
        r_cols[3].write(str(row["Transmitida por"]).strip())
        r_cols[4].write(str(row.get("Data Transmissão", "")).strip()[:10])

        # ==============================================================
        # BUSCA DEC E REC
        # ==============================================================
        arquivos_encontrados = []

        if os.path.exists(DOCS):
            cpf_limpo = "".join(c for c in cpf if c.isdigit())

            if cpf_limpo:
                for f in os.listdir(DOCS):
                    nome_arquivo = f.lower()

                    if (
                        f.startswith(cpf_limpo)
                        and (
                            nome_arquivo.endswith(".dec")
                            or nome_arquivo.endswith(".rec")
                        )
                    ):
                        arquivos_encontrados.append(
                            os.path.join(DOCS, f)
                        )

        # ==============================================================
        # DOWNLOAD
        # ==============================================================
        with r_cols[5]:
            if arquivos_encontrados:
                zip_buffer = io.BytesIO()

                with zipfile.ZipFile(
                    zip_buffer,
                    "w",
                    zipfile.ZIP_DEFLATED
                ) as zip_file:
                    for arq in arquivos_encontrados:
                        zip_file.write(
                            arq,
                            arcname=os.path.basename(arq)
                        )

                zip_buffer.seek(0)

                st.download_button(
                    label="⬇️ Baixar",
                    data=zip_buffer,
                    file_name=f"IRPF_{cpf}.zip",
                    mime="application/zip",
                    key=f"dl_{cpf}_{idx}",
                    use_container_width=True
                )
            else:
                st.markdown(
                    "<span style='color: #ef4444; font-size: 0.8rem;'>❌ Indisponível</span>",
                    unsafe_allow_html=True
                )

        st.markdown(
            "<hr style='margin: 5px 0; border-color: #1e293b;'>",
            unsafe_allow_html=True
        )

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown(f"""
<div class="dashboard-footer">
  Gerado em {datetime.now().strftime("%d/%m/%Y %H:%M:%S")} &nbsp;·&nbsp;
  Fonte: {os.path.basename(ARQ_PLANILHA_FINAL)} &nbsp;·&nbsp;
  {total_registros} registros filtrados do catálogo ({len(df_original)} total)
</div>
""", unsafe_allow_html=True)
