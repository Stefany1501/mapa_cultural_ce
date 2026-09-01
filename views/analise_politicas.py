import requests
import pandas as pd
import streamlit as st
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import re
import unicodedata
from pathlib import Path

# Configuração usada quando este painel é executado isoladamente. Na aplicação
# integrada, a configuração global é feita antes de carregar o painel escolhido.
if __name__ == "__main__":
    st.set_page_config(page_title="Análise de Políticas Culturais", layout="wide")

# configuracao api e arquivo xslx
API_BASE = "https://mapacultural.secult.ce.gov.br/api"
SALIC_API_BASE = "https://api.salic.cultura.gov.br/api/v1"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
XLSX_PATH = PROJECT_ROOT / "data" / "raw" / "pnab" / "adesao_aldir.xlsx"
CSV_MUN_LPG = PROJECT_ROOT / "data" / "raw" / "lpg" / "adesao_municipios.csv"
CSV_EST_LPG = PROJECT_ROOT / "data" / "raw" / "lpg" / "adesao_estados.csv"

HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

session = requests.Session()
session.headers.update(HEADERS)

session_salic = requests.Session()
session_salic.headers.update(HEADERS)

# termos de busca e stopwords
TERMOS_COVID = ["covid ", "covid-19 ", "covid19 ", "coronavírus ", "coronavirus ", "pandemia ", "pandêmico ", "emergência ", "emergencia ", "emergencial ", "isolamento ", "quarentena ", "distanciamento "]
TERMOS_LEI_ALDIR = ["aldir blanc ", "lei aldir ", "lei nº 14.017 ", "lei 14.017 ", "lei 14017 ", "política nacional aldir blanc ", "pnab "]
TERMOS_LEI_ROUANET = ["rouanet ", "lei rouanet ", "lei 8.313 ", "lei nº 8.313 ", "lei 8313 ", "incentivo fiscal ", "incentivo à cultura ", "pronac ", "renúncia fiscal ", "patrocínio cultural ", "mecenato ", "dedução fiscal ", "irrf cultural "]

STOPWORDS = set(['a', 'o', 'que', 'e', 'do', 'da', 'em', 'um', 'para', 'é', 'com', 'não', 'uma', 'os', 'no', 'se', 'na', 'por', 'mais', 'as', 'dos', 'como', 'mas', 'foi', 'ao', 'ele', 'das', 'tem', 'à', 'seu', 'sua', 'ou', 'ser', 'quando', 'muito', 'há', 'nos', 'está', 'eu', 'também', 'só', 'pelo', 'pela', 'até', 'isso', 'ela', 'entre', 'era', 'depois', 'sem', 'mesmo', 'aos', 'ter', 'seus', 'quem', 'nas', 'me', 'esse', 'eles', 'estão', 'você', 'tinha', 'foram', 'essa', 'num', 'nem', 'suas', 'meu', 'às', 'minha', 'têm', 'numa', 'pelos', 'elas', 'havia', 'seja', 'qual', 'será', 'nós', 'tenho', 'lhe', 'deles', 'essas', 'esses', 'pelas', 'este', 'fosse', 'dele', 'vocês', 'vos', 'lhes', 'meus', 'minhas', 'teu', 'tua', 'teus', 'tuas', 'nosso', 'nossa', 'nossos', 'nossas', 'dela', 'delas', 'esta', 'estes', 'estas', 'aquele', 'aquela', 'aqueles', 'aquelas', 'isto', 'aquilo', 'estou', 'está', 'estamos', 'estão', 'estive', 'esteve', 'estivemos', 'estiveram', 'estava', 'estávamos', 'estavam', 'estivera', 'estivéramos', 'esteja', 'estejamos', 'estejam', 'estivesse', 'estivéssemos', 'estivessem', 'estiver', 'estivermos', 'estiverem', 'hei', 'há', 'havemos', 'hão', 'houve', 'houvemos', 'houveram', 'houvera', 'houvéramos', 'haja', 'hajamos', 'hajam', 'houvesse', 'houvéssemos', 'houvessem', 'houver', 'houvermos', 'houverem', 'houverei', 'houverá', 'houveremos', 'houverão', 'houveria', 'houveríamos', 'houveriam', 'sou', 'somos', 'são', 'era', 'éramos', 'eram', 'fui', 'fomos', 'fora', 'fôramos', 'sejamos', 'sejam', 'fôssemos', 'fossem', 'for', 'formos', 'forem', 'serei', 'será', 'seremos', 'serão', 'seria', 'seríamos', 'seriam', 'temos', 'têm', 'tínhamos', 'tinham', 'tive', 'teve', 'tivemos', 'tiveram', 'tivera', 'tivéramos', 'tenha', 'tenhamos', 'tenham', 'tivesse', 'tivéssemos', 'tivessem', 'tiver', 'tivermos', 'tiverem', 'terei', 'terá', 'teremos', 'terão', 'teria', 'teríamos', 'teriam', 'edital', 'projeto', 'proposta', 'cultural', 'cultura', 'inscrição', 'inscrições', 'participar', 'participação', 'ceará', 'estado', 'município', 'valor', 'recursos'])

# funcoes auxiliares
def converter_data(valor):
    try:
        if valor is None: return pd.NaT
        if not isinstance(valor, (dict, list)):
            try:
                if pd.isna(valor): return pd.NaT
            except: pass
        if isinstance(valor, dict):
            if "timestamp" in valor: return pd.to_datetime(int(valor["timestamp"]), unit="s")
            if "date" in valor: return pd.to_datetime(valor["date"], errors="coerce")
        return pd.to_datetime(valor, errors="coerce")
    except: return pd.NaT

def buscar_termos_texto(texto, termos_busca):
    if pd.isna(texto) or not isinstance(texto, str): return []
    texto_lower = texto.lower()
    return [termo for termo in termos_busca if termo.lower() in texto_lower]

def limpar_texto(texto):
    if pd.isna(texto) or not isinstance(texto, str): return ""
    texto = texto.lower()
    texto = re.sub(r'<[^>]+>', '', texto)
    texto = re.sub(r'http\S+|www\S+', '', texto)
    texto = re.sub(r'[^a-záàâãéèêíïóôõöúçñ\s]', ' ', texto)
    texto = re.sub(r'\b\w{1,2}\b', '', texto)
    return texto.strip()

def normalizar_nome(nome: str) -> str:
    if pd.isna(nome) or not isinstance(nome, str): return ""
    nome = nome.lower()
    nome = re.sub(r'[áàâãä]', 'a', nome)
    nome = re.sub(r'[éèêë]', 'e', nome)
    nome = re.sub(r'[íìîï]', 'i', nome)
    nome = re.sub(r'[óòôõö]', 'o', nome)
    nome = re.sub(r'[úùûü]', 'u', nome)
    nome = re.sub(r'[ç]', 'c', nome)
    nome = re.sub(r'[^a-z0-9\s]', '', nome)
    palavras_comuns = {'de', 'da', 'do', 'das', 'dos', 'e', 'para', 'com', 'em', 'no', 'na'}
    return ' '.join([p for p in nome.split() if p not in palavras_comuns and len(p) > 2]).strip()

def fmt_brl(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def buscar_dados_paginados(url, params_base, mensagem="Carregando dados da API..."):
    dados_completos, offset, limit = [], 0, min(params_base.get("@limit", 500), 500)
    params_base["@limit"] = limit
    with st.spinner(mensagem):
        while True:
            params = params_base.copy()
            params["@offset"] = offset
            try:
                resposta = session.get(url, params=params, timeout=30)
                resposta.raise_for_status()
                lote = resposta.json()
                if not isinstance(lote, list) or len(lote) == 0: break
                dados_completos.extend(lote)
                if len(lote) < limit: break
                offset += limit
            except Exception as e:
                st.error(f"Erro na paginação do Mapa Cultural: {e}")
                break
    return dados_completos

def processar_dataframe_mapa(lote, nome_col_ano):
    if not lote:
        return pd.DataFrame(columns=["id", "name", "shortDescription", "longDescription", "createTimestamp", "createTimestamp_dt", nome_col_ano])
    df = pd.DataFrame(lote)
    for col in ["createTimestamp", "shortDescription", "longDescription", "name"]:
        if col not in df.columns: df[col] = None
    df["createTimestamp_dt"] = df["createTimestamp"].apply(converter_data)
    df[nome_col_ano] = df["createTimestamp_dt"].dt.year
    return df

@st.cache_data(ttl=3600, show_spinner=False)
def carregar_dados_mapa_cultural():
    """Busca e estrutura todas as entidades do Mapa Cultural do CE com descrição."""
    df_opp = processar_dataframe_mapa(buscar_dados_paginados(f"{API_BASE}/opportunity/find", {"@select": "id,name,shortDescription,longDescription,createTimestamp", "status": "EQ(1)", "@limit": 500}, "Coletando Editais (Oportunidades)..."), "ano_criacao")
    df_agentes = processar_dataframe_mapa(buscar_dados_paginados(f"{API_BASE}/agent/find", {"@select": "id,name,shortDescription,longDescription,createTimestamp,En_Municipio", "@limit": 500}, "Coletando Perfis de Agentes Culturais..."), "ano")
    df_espacos = processar_dataframe_mapa(buscar_dados_paginados(f"{API_BASE}/space/find", {"@select": "id,name,shortDescription,longDescription,createTimestamp", "@limit": 500}, "Coletando Espaços Culturais..."), "ano")
    df_eventos = processar_dataframe_mapa(buscar_dados_paginados(f"{API_BASE}/event/find", {"@select": "id,name,shortDescription,longDescription,createTimestamp", "@limit": 500}, "Coletando Eventos Culturais..."), "ano")
    df_projetos = processar_dataframe_mapa(buscar_dados_paginados(f"{API_BASE}/project/find", {"@select": "id,name,shortDescription,longDescription,createTimestamp", "@limit": 500}, "Coletando Projetos Culturais..."), "ano")
    return df_opp, df_agentes, df_espacos, df_eventos, df_projetos

# extracao leis
@st.cache_data(ttl=3600, show_spinner=False)
def buscar_projetos_salic(ano_projeto=2021, uf=None):
    todos_projetos = []
    limit, offset, total_registros, max_retries = 100, 0, None, 3
    ano_formatado = str(ano_projeto)[-2:] if ano_projeto else None
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    while True:
        params = {"limit": limit, "offset": offset}
        if uf:
            params["uf"] = uf
        if ano_formatado: params["ano_projeto"] = ano_formatado

        tentativa, sucesso, lote_projetos = 0, False, []
        while tentativa < max_retries and not sucesso:
            try:
                status_text.text(f"Buscando projetos Rouanet do servidor... (Deslocamento: {offset})")
                resposta = session_salic.get(f"{SALIC_API_BASE}/projetos", params=params, timeout=20)
                if resposta.status_code == 404:
                    sucesso = True
                    break
                resposta.raise_for_status()
                dados = resposta.json()
                lote_projetos = dados.get("_embedded", {}).get("projetos", [])
                if total_registros is None:
                    total_registros = dados.get("total", 0)
                    if total_registros == 0: break
                sucesso = True
            except:
                tentativa += 1
                import time
                time.sleep(1)
        
        if not sucesso or not lote_projetos: break
        todos_projetos.extend(lote_projetos)
        
        if total_registros:
            progress_bar.progress(min(offset / total_registros, 1.0))
        offset += limit
        if offset >= total_registros or len(lote_projetos) < limit: break
            
    progress_bar.empty()
    status_text.empty()

    if not todos_projetos: return pd.DataFrame()

    dados_processados = []
    for p in todos_projetos:
        locais = p.get("local_realizacao", [])
        municipios_execucao = []

        if isinstance(locais, list):
            for local in locais:
                uf_local = str(local.get("UF", local.get("uf", ""))).upper()
                muni = local.get("municipio")
                if muni:
                    municipios_execucao.append(f"{muni}/{uf_local}" if uf_local else str(muni))
        municipio_execucao = ", ".join(dict.fromkeys(municipios_execucao)) or p.get("municipio", "Não informado")

        dados_processados.append({
            "PRONAC": p.get("PRONAC"), "nome": p.get("nome"), "proponente": p.get("proponente"),
            "uf_origem": p.get("UF"), "municipio_origem": p.get("municipio"), "municipio_execucao": municipio_execucao,
            "area": p.get("area"), "segmento": p.get("segmento"), "ano_projeto": p.get("ano_projeto"),
            "valor_aprovado": p.get("valor_aprovado", 0), "valor_captado": p.get("valor_captado", 0)
        })

    df = pd.DataFrame(dados_processados)
    for col in ["valor_aprovado", "valor_captado"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df

@st.cache_data(show_spinner=False)
def carregar_aldir_blanc(caminho_xlsx: str) -> pd.DataFrame:
    df = pd.read_excel(caminho_xlsx, header=4, skiprows=[5])
    df = df.rename(columns={
        "Ano de Adesão": "ciclo", "Tipo do Ente": "tipo_ente", "Código IBGE": "codigo_ibge",
        "População": "populacao", "UF do Ente": "uf", "Nome do Ente": "nome_ente",
        "Aderiu a política?": "aderiu", "Situação Plano de Ação": "situacao_plano",
        "Valor do Plano de Ação": "valor_plano", "Situação do Termo de Adesão": "situacao_termo"
    })
    df = df[df["tipo_ente"].isin(["Estado", "Município"])].copy()
    df["valor_plano"] = pd.to_numeric(df["valor_plano"], errors="coerce").fillna(0)
    df["populacao"] = pd.to_numeric(df["populacao"], errors="coerce")
    return df

@st.cache_data(show_spinner=False)
def carregar_lei_paulo_gustavo(caminho_mun: str, caminho_est: str):
    """Carrega integralmente os dois arquivos CSV da Lei Paulo Gustavo."""
    df_mun = pd.read_csv(caminho_mun)
    df_est = pd.read_csv(caminho_est)
    df_mun["Valor Disponível"] = pd.to_numeric(df_mun["Valor Disponível"], errors="coerce").fillna(0)
    df_est["Valor Disponível"] = pd.to_numeric(df_est["Valor Disponível"], errors="coerce").fillna(0)
    return df_mun, df_est

def normalizar_municipio(valor):
    if pd.isna(valor): return ""
    texto = unicodedata.normalize("NFKD", str(valor)).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]", "", texto.lower())

def cruzar_municipios_com_agentes(df_municipios, coluna_municipio, df_agentes):
    """Relaciona entes municipais a agentes do Mapa por município normalizado."""
    if df_municipios.empty or df_agentes.empty or "En_Municipio" not in df_agentes.columns:
        return pd.DataFrame()
    municipios = df_municipios.copy()
    agentes = df_agentes.copy()
    municipios["municipio_chave"] = municipios[coluna_municipio].apply(normalizar_municipio)
    agentes["municipio_chave"] = agentes["En_Municipio"].apply(normalizar_municipio)
    contagem = agentes[agentes["municipio_chave"] != ""].groupby("municipio_chave").size().rename("agentes_mapa")
    return municipios.merge(contagem, on="municipio_chave", how="left").assign(
        agentes_mapa=lambda df: df["agentes_mapa"].fillna(0).astype(int)
    )

def cruzar_agentes_projetos(df_agentes, df_salic):
    if df_agentes.empty or df_salic.empty: return pd.DataFrame()
    df_agentes["nome_normalizado"] = df_agentes["name"].apply(normalizar_nome)
    df_salic["proponente_normalizado"] = df_salic["proponente"].apply(normalizar_nome)
    
    agentes_dict = {}
    for _, row in df_agentes.iterrows():
        nome_norm = row["nome_normalizado"]
        if nome_norm:
            if nome_norm not in agentes_dict: agentes_dict[nome_norm] = []
            agentes_dict[nome_norm].append(row)
    
    matches = []
    for _, project in df_salic.iterrows():
        proponente_norm = project["proponente_normalizado"]
        if proponente_norm in agentes_dict:
            for agente in agentes_dict[proponente_norm]:
                matches.append({
                    "PRONAC": project["PRONAC"], "nome_projeto": project["nome"], "proponente_salic": project["proponente"],
                    "valor_aprovado": project["valor_aprovado"], "valor_captado": project["valor_captado"],
                    "agente_id": agente["id"], "agente_nome": agente["name"]
                })
    return pd.DataFrame(matches)

# interface principal
st.title("Painel Integrado de Políticas Culturais — CE")

# Carga de todas as bases expandidas do Mapa Cultural
df_oportunidades, df_agentes, df_espacos, df_eventos, df_projetos = carregar_dados_mapa_cultural()

if df_oportunidades.empty:
    st.warning("Falha ao carregar a base de oportunidades do Mapa Cultural.")
    st.stop()

# definindo abas
tab1, tab2_geral, tab2, tab3_geral, tab3, tab4_geral, tab4 = st.tabs([
    "Mapa Cultural", "Rouanet — Brasil", "Rouanet — Ceará + Mapa",
    "PNAB — Brasil", "PNAB — Ceará + Mapa", "LPG — Brasil", "LPG — Ceará + Mapa"
])

# aba 1 - analise textual e de contexto
with tab1:
    editais_2021 = df_oportunidades[df_oportunidades["ano_criacao"] == 2021].copy()
    st.subheader(f"Métricas de Editais Publicados em 2021")
    
    if not editais_2021.empty:
        editais_2021["termos_covid"] = editais_2021.apply(lambda r: buscar_termos_texto(f"{r.get('shortDescription','')} {r.get('longDescription','')}", TERMOS_COVID), axis=1)
        editais_2021["termos_lei_aldir"] = editais_2021.apply(lambda r: buscar_termos_texto(f"{r.get('shortDescription','')} {r.get('longDescription','')}", TERMOS_LEI_ALDIR), axis=1)
        editais_2021["termos_lei_rouanet"] = editais_2021.apply(lambda r: buscar_termos_texto(f"{r.get('shortDescription','')} {r.get('longDescription','')}", TERMOS_LEI_ROUANET), axis=1)

        editais_2021["menciona_covid"] = editais_2021["termos_covid"].apply(len) > 0
        editais_2021["menciona_lei_aldir"] = editais_2021["termos_lei_aldir"].apply(len) > 0
        editais_2021["menciona_lei_rouanet"] = editais_2021["termos_lei_rouanet"].apply(len) > 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Editais em 2021", len(editais_2021))
        m2.metric("Mencionam COVID-19", int(editais_2021["menciona_covid"].sum()))
        m3.metric("Mencionam Lei Aldir Blanc", int(editais_2021["menciona_lei_aldir"].sum()))
        m4.metric("Mencionam Lei Rouanet", int(editais_2021["menciona_lei_rouanet"].sum()))

        st.markdown("---")
        st.subheader("Comparativo de Menções entre Modelos de Políticas Públicas")
        dados_comparativo = pd.DataFrame({
            "Política": ["Lei Aldir Blanc / PNAB", "Lei Rouanet (Incentivo Fiscal)"],
            "Editais que mencionam": [int(editais_2021["menciona_lei_aldir"].sum()), int(editais_2021["menciona_lei_rouanet"].sum())]
        })
        fig_comp = px.bar(dados_comparativo, x="Política", y="Editais que mencionam", text="Editais que mencionam", color="Política", color_discrete_map={"Lei Aldir Blanc / PNAB": "#3498db", "Lei Rouanet (Incentivo Fiscal)": "#f39c12"})
        fig_comp.update_traces(textposition="outside")
        fig_comp.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)", yaxis_title="Quantidade de Editais")
        st.plotly_chart(fig_comp, use_container_width=True)

        st.markdown("---")
        st.subheader("Nuvens de Palavras por Entidade (Foco Histórico 2021)")
        st.markdown("Análise textual comparativa baseada nas descrições de cada entidade cadastrada no Mapa Cultural:")
        
        # mapeamento estático estruturado para o loop sequencial
        mapa_entidades = {
            "Editais (Oportunidades)": (editais_2021, "ano_criacao", "Reds"),
            "Agentes Culturais": (df_agentes, "ano", "Blues"),
            "Espaços Culturais": (df_espacos, "ano", "Greens"),
            "Eventos": (df_eventos, "ano", "Purples"),
            "Projetos Culturais": (df_projetos, "ano", "Oranges")
        }
        
        for nome_entidade, (df_alvo, col_ano, paleta_cor) in mapa_entidades.items():
            # filtro por ano para manter consistência com o escopo de 2021
            df_filtrado_2021 = df_alvo if nome_entidade == "Editais (Oportunidades)" else df_alvo[df_alvo[col_ano] == 2021]
            
            textos_entidade = []
            for _, row in df_filtrado_2021.iterrows():
                if pd.notna(row.get("shortDescription")): textos_entidade.append(str(row["shortDescription"]))
                if pd.notna(row.get("longDescription")): textos_entidade.append(str(row["longDescription"]))
                
            texto_limpo = limpar_texto(" ".join(textos_entidade))
            
            st.markdown(f"### {nome_entidade}")
            if len(texto_limpo) > 15:
                wc = WordCloud(width=1200, height=350, background_color="white", stopwords=STOPWORDS, max_words=100, colormap=paleta_cor, collocations=False).generate(texto_limpo)
                fig_wc, ax = plt.subplots(figsize=(14, 4))
                ax.imshow(wc, interpolation="bilinear")
                ax.axis("off")
                st.pyplot(fig_wc)
                plt.close(fig_wc)
            else:
                st.info(f"Registros textuais insuficientes para gerar a nuvem para a entidade '{nome_entidade}' no ano de 2021.")
            st.markdown(" ")
        # ───────────────────────────────────────────────────────────────────

        st.subheader("Evolução Mensal de Cadastros de Agentes (2021)")
        if not df_agentes.empty and "ano" in df_agentes.columns:
            agentes_2021 = df_agentes[(df_agentes["ano"] == 2021) & (df_agentes["createTimestamp_dt"].notna())].copy()
            if not agentes_2021.empty:
                agentes_2021["mes"] = agentes_2021["createTimestamp_dt"].dt.to_period("M")
                cadastros_mensais = agentes_2021.groupby("mes").size().reset_index(name="quantidade")
                cadastros_mensais["mes"] = cadastros_mensais["mes"].dt.to_timestamp()
                fig_mensal = px.line(cadastros_mensais, x="mes", y="quantidade", markers=True, text="quantidade")
                fig_mensal.update_traces(textposition="top center")
                st.plotly_chart(fig_mensal, use_container_width=True)

# Lei Rouanet — panorama da base original, sem recorte territorial ou cruzamento
with tab2_geral:
    st.subheader("Lei Rouanet — panorama nacional antes do cruzamento")
    anos_disponiveis = [2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]
    ano_rouanet_br = st.selectbox("Ano do projeto:", anos_disponiveis, index=2, key="ano_rouanet_br")
    df_salic_br = buscar_projetos_salic(ano_projeto=ano_rouanet_br)
    if df_salic_br.empty:
        st.info(f"Nenhum projeto localizado para {ano_rouanet_br}.")
    else:
        rb1, rb2, rb3 = st.columns(3)
        rb1.metric("Projetos no Brasil", f"{len(df_salic_br):,}".replace(",", "."))
        rb2.metric("Total aprovado", fmt_brl(df_salic_br["valor_aprovado"].sum()))
        rb3.metric("Total captado", fmt_brl(df_salic_br["valor_captado"].sum()))
        por_uf = df_salic_br["uf_origem"].fillna("Não informado").value_counts().head(15).reset_index()
        por_uf.columns = ["UF", "Projetos"]
        st.plotly_chart(px.bar(por_uf, x="UF", y="Projetos", text="Projetos", title="Projetos por UF de origem — top 15"), use_container_width=True)
        st.dataframe(df_salic_br, use_container_width=True, hide_index=True)

# aba 2 - lei rouanet: recorte CE e cruzamento nominal
with tab2:
    st.subheader("Análise de Projetos Captados via Lei Rouanet (Federal)")
    
    anos_disponiveis = [2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]
    ano_selecionado = st.selectbox("Filtrar Ano de Execução do Projeto:", options=anos_disponiveis, index=anos_disponiveis.index(2021), key="ano_rouanet_ce")
    
    df_salic = buscar_projetos_salic(ano_projeto=ano_selecionado, uf="CE")
    
    if df_salic.empty:
        st.info(f"Nenhum registro localizado para o ano {ano_selecionado} com as diretrizes do Ceará.")
    else:
        col_r1, col_r2, col_r3 = st.columns(3)
        col_r1.metric("Volume de Projetos", f"{len(df_salic)}")
        col_r2.metric("Total Aprovado", fmt_brl(df_salic["valor_aprovado"].sum()))
        col_r3.metric("Total Captado", fmt_brl(df_salic["valor_captado"].sum()))
        
        st.markdown("---")
        st.subheader("Distribuição Territorial de Origem dos Proponentes")
        mun_counts = df_salic["municipio_origem"].value_counts().head(10).reset_index()
        mun_counts.columns = ["Município", "Quantidade"]
        fig_origem = px.bar(mun_counts, x="Município", y="Quantidade", color="Município", color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_origem, use_container_width=True)
        
        if not df_agentes.empty:
            st.markdown("---")
            st.subheader("Cruzamento de Proponentes Federais com a Base de Agentes Estaduais")
            df_matches = cruzar_agentes_projetos(df_agentes, df_salic)
            
            if not df_matches.empty:
                st.success(f"Foram identificados {len(df_matches)} cruzamentos exatos de nomes entre as bases.")
                st.metric("Agentes Únicos Localizados", df_matches["agente_nome"].nunique())
                
                st.markdown("#### Relação de Agentes Identificados no Mapa Cultural")
                df_matches_exibicao = df_matches[[
                    "agente_nome", "proponente_salic", "PRONAC", "nome_projeto", "valor_captado"
                ]].copy().rename(columns={
                    "agente_nome": "Nome do Agente (Mapa Cultural)", "proponente_salic": "Proponente (SALIC)",
                    "PRONAC": "PRONAC", "nome_projeto": "Nome do Projeto Federal", "valor_captado": "Valor Captado (R$)"
                })
                df_matches_exibicao["Valor Captado (R$)"] = df_matches_exibicao["Valor Captado (R$)"].apply(fmt_brl)
                st.dataframe(df_matches_exibicao, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum cruzamento de nomes idênticos foi encontrado entre as duas bases para o ano selecionado.")
        
        st.markdown("---")
        st.subheader("Tabela Geral de Projetos Executados no Ceará")
        df_exib_salic = pd.DataFrame({
            "PRONAC": df_salic["PRONAC"],
            "Nome do Projeto": df_salic["nome"],
            "Proponente": df_salic["proponente"],
            "UF Origem": df_salic["uf_origem"],
            "Município Origem": df_salic["municipio_origem"],
            "Município de Execução (CE)": df_salic["municipio_execucao"],
            "Segmento": df_salic["segmento"],
            "Valor Aprovado": df_salic["valor_aprovado"].apply(fmt_brl),
            "Valor Captado": df_salic["valor_captado"].apply(fmt_brl)
        })
        st.dataframe(df_exib_salic, use_container_width=True, hide_index=True)

# PNAB — panorama nacional da planilha original
with tab3_geral:
    st.subheader("PNAB — panorama nacional antes do cruzamento")
    try:
        df_aldir_br = carregar_aldir_blanc(XLSX_PATH)
        ciclos_br = sorted(df_aldir_br["ciclo"].dropna().unique())
        ciclo_br = st.selectbox("Ciclo:", ["Todos"] + list(ciclos_br), key="ciclo_pnab_br")
        df_pnab_br = df_aldir_br if ciclo_br == "Todos" else df_aldir_br[df_aldir_br["ciclo"] == ciclo_br]
        pb1, pb2, pb3 = st.columns(3)
        pb1.metric("Entes federados", f"{len(df_pnab_br):,}".replace(",", "."))
        pb2.metric("Municípios", f"{(df_pnab_br['tipo_ente'] == 'Município').sum():,}".replace(",", "."))
        pb3.metric("Valor dos planos", fmt_brl(df_pnab_br["valor_plano"].sum()))
        uf_pnab = df_pnab_br.groupby("uf", dropna=False)["valor_plano"].sum().nlargest(15).reset_index()
        st.plotly_chart(px.bar(uf_pnab, x="uf", y="valor_plano", title="Valor dos planos por UF — top 15"), use_container_width=True)
        st.dataframe(df_pnab_br, use_container_width=True, hide_index=True)
    except FileNotFoundError:
        st.error(f"Arquivo **{XLSX_PATH}** não localizado.")

# aba 3 - lei aldir: recorte CE e integração territorial
with tab3:
    st.subheader("Adesão Histórica à Política Nacional Aldir Blanc (PNAB)")
    try:
        df_aldir = carregar_aldir_blanc(XLSX_PATH)
        df_ce = df_aldir[df_aldir["uf"] == "CE"].copy()
        
        if df_ce.empty:
            st.warning("Planilha lida com sucesso, mas nenhum dado mapeado para a UF 'CE'.")
        else:
            ciclos = sorted(df_ce["ciclo"].dropna().unique())
            ciclo_sel = st.selectbox("Filtrar Ciclo de Repasse:", options=["Todos"] + list(ciclos), index=0)
            
            df_f_aldir = df_ce if ciclo_sel == "Todos" else df_ce[df_ce["ciclo"] == ciclo_sel]
            df_est = df_f_aldir[df_f_aldir["tipo_ente"] == "Estado"]
            df_mun = df_f_aldir[df_f_aldir["tipo_ente"] == "Município"]
            
            ca1, ca2, ca3 = st.columns(3)
            ca1.metric("Repasse Global (CE)", fmt_brl(df_f_aldir["valor_plano"].sum()))
            ca2.metric("Destinado ao Estado", fmt_brl(df_est["valor_plano"].sum()))
            ca3.metric("Destinado aos Municípios", fmt_brl(df_mun["valor_plano"].sum()))
            
            st.markdown("---")
            st.subheader("Maiores Destinações Orçamentárias por Município do Ceará")
            top_mun = df_mun.groupby("nome_ente")["valor_plano"].sum().sort_values(ascending=False).head(15).reset_index()
            top_mun.columns = ["Município", "Valor"]
            fig_top_mun = px.bar(top_mun, x="Valor", y="Município", orientation="h", color="Valor", color_continuous_scale="Blues")
            fig_top_mun.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_top_mun, use_container_width=True)
            
            st.subheader("Planilha Consolidada de Metas de Planos de Ação")
            df_exib_aldir = df_f_aldir[["ciclo", "tipo_ente", "nome_ente", "populacao", "situacao_plano", "valor_plano"]].copy().rename(columns={
                "ciclo": "Ciclo", "tipo_ente": "Tipo Ente", "nome_ente": "Nome", "populacao": "População", "situacao_plano": "Situação do Plano", "valor_plano": "Orçamento Declarado (R$)"
            })
            st.dataframe(df_exib_aldir, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.subheader("Cruzamento territorial com agentes do Mapa Cultural")
            df_pnab_mapa = cruzar_municipios_com_agentes(df_mun, "nome_ente", df_agentes)
            if df_pnab_mapa.empty:
                st.info("O Mapa Cultural não retornou o campo municipal necessário para o cruzamento.")
            else:
                st.metric("Municípios com agentes localizados", int((df_pnab_mapa["agentes_mapa"] > 0).sum()))
                st.dataframe(df_pnab_mapa[["nome_ente", "valor_plano", "agentes_mapa"]].rename(columns={"nome_ente": "Município", "valor_plano": "Valor do plano", "agentes_mapa": "Agentes no Mapa"}), use_container_width=True, hide_index=True)
            
    except FileNotFoundError:
        st.error(f"Arquivo local obrigatório **{XLSX_PATH}** não foi localizado na raiz do projeto. Insira-o para carregar esta aba.")
        
# LPG — panorama nacional dos CSV originais
with tab4_geral:
    st.subheader("Lei Paulo Gustavo — panorama nacional antes do cruzamento")
    try:
        df_mun_lpg_br, df_est_lpg_br = carregar_lei_paulo_gustavo(CSV_MUN_LPG, CSV_EST_LPG)
        lb1, lb2, lb3 = st.columns(3)
        lb1.metric("Municípios na base", f"{len(df_mun_lpg_br):,}".replace(",", "."))
        lb2.metric("Estados na base", f"{len(df_est_lpg_br):,}".replace(",", "."))
        lb3.metric("Valor disponível", fmt_brl(df_mun_lpg_br["Valor Disponível"].sum() + df_est_lpg_br["Valor Disponível"].sum()))
        lpg_uf = df_mun_lpg_br.groupby("UF")["Valor Disponível"].sum().sort_values(ascending=False).reset_index()
        st.plotly_chart(px.bar(lpg_uf, x="UF", y="Valor Disponível", title="Recursos municipais por UF"), use_container_width=True)
        st.dataframe(df_mun_lpg_br, use_container_width=True, hide_index=True)
    except FileNotFoundError:
        st.error("Arquivos CSV da LPG não localizados.")

# aba 4 - lei paulo gustavo: recorte CE e integração territorial
with tab4:
    st.subheader("Acompanhamento da Lei Paulo Gustavo (LPG) — Ceará")
    st.markdown(
        "Monitoramento físico-financeiro de liberação orçamentária da Lei Complementar nº 195/2022. "
        "Dados extraídos diretamente dos relatórios federais de homologação e adesão das contas cearenses."
    )
    
    try:
        df_mun_lpg, df_est_lpg = carregar_lei_paulo_gustavo(CSV_MUN_LPG, CSV_EST_LPG)
        df_mun_lpg_ce = df_mun_lpg[df_mun_lpg["UF"] == "CE"].copy()
        df_est_lpg_ce = df_est_lpg[df_est_lpg["Estado"].astype(str).str.upper() == "CEARA"].copy()
        
        if df_mun_lpg_ce.empty and df_est_lpg_ce.empty:
            st.warning("Dados lidos com sucesso, mas nenhum registro do Ceará foi identificado.")
        else:
            # cálculos de métricas
            valor_lpg_estado = df_est_lpg_ce["Valor Disponível"].sum() if not df_est_lpg_ce.empty else 0
            valor_lpg_municipios = df_mun_lpg_ce["Valor Disponível"].sum()
            total_lpg_ce = valor_lpg_estado + valor_lpg_municipios
            
            municipios_autorizados = len(df_mun_lpg_ce[df_mun_lpg_ce["Situação do Plano"] == "Autorizado"])
            total_municipios_base = len(df_mun_lpg_ce)
            
            # renderização de indicadores
            cl1, cl2, cl3, cl4 = st.columns(4)
            cl1.metric("Orçamento Total LPG (CE)", fmt_brl(total_lpg_ce))
            cl2.metric("Destinado ao Estado (Secult CE)", fmt_brl(valor_lpg_estado))
            cl3.metric("Destinado aos 184 Municípios", fmt_brl(valor_lpg_municipios))
            cl4.metric("Planos Autorizados pelo MinC", f"{municipios_autorizados} / {total_municipios_base}")
            
            st.markdown("---")
            
            # gráfico de maiores municípios beneficiados
            st.subheader("Top 15 Municípios com Maiores Recursos Disponíveis")
            df_top_lpg = df_mun_lpg_ce.sort_values(by="Valor Disponível", ascending=False).head(15)
            
            fig_top_lpg = px.bar(
                df_top_lpg,
                x="Valor Disponível",
                y="Município",
                orientation="h",
                text_auto=".3s",
                color="Valor Disponível",
                color_continuous_scale="Oranges",
                labels={"Valor Disponível": "Valor Disponível (R$)"}
            )
            fig_top_lpg.update_layout(
                yaxis=dict(autorange="reversed"),
                showlegend=False,
                coloraxis_showscale=False,
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=20, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_top_lpg, use_container_width=True)
            
            st.markdown("---")
            
            # pizza de status de planos
            st.subheader("Distribuição de Situação dos Planos de Ação Municipais")
            sit_counts_lpg = df_mun_lpg_ce["Situação do Plano"].value_counts().reset_index()
            sit_counts_lpg.columns = ["Situação", "Quantidade"]
            
            fig_sit_lpg = px.pie(
                sit_counts_lpg,
                values="Quantidade",
                names="Situação",
                color_discrete_sequence=["#e67e22", "#34495e", "#f1c40f"]
            )
            fig_sit_lpg.update_traces(textposition="inside", textinfo="percent+label")
            fig_sit_lpg.update_layout(showlegend=False)
            st.plotly_chart(fig_sit_lpg, use_container_width=True)
            
            st.markdown("---")
            
            # tabela detalhada
            st.subheader("Planilha Consolidada de Recursos — LPG")
            
            df_exib_lpg_fmt = df_mun_lpg_ce[["Município", "Situação do Plano", "Valor Disponível"]].copy()
            df_exib_lpg_fmt = df_exib_lpg_fmt.sort_values(by="Valor Disponível", ascending=False)
            
            # formatação amigável para renderização em tela
            df_exib_lpg_fmt["Recursos Alocados (R$)"] = df_exib_lpg_fmt["Valor Disponível"].apply(fmt_brl)
            df_exib_lpg_fmt = df_exib_lpg_fmt.drop(columns=["Valor Disponível"])
            
            st.dataframe(df_exib_lpg_fmt, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.subheader("Cruzamento territorial com agentes do Mapa Cultural")
            df_lpg_mapa = cruzar_municipios_com_agentes(df_mun_lpg_ce, "Município", df_agentes)
            if df_lpg_mapa.empty:
                st.info("O Mapa Cultural não retornou o campo municipal necessário para o cruzamento.")
            else:
                st.metric("Municípios com agentes localizados", int((df_lpg_mapa["agentes_mapa"] > 0).sum()))
                st.dataframe(df_lpg_mapa[["Município", "Valor Disponível", "Situação do Plano", "agentes_mapa"]].rename(columns={"agentes_mapa": "Agentes no Mapa"}), use_container_width=True, hide_index=True)
            
    except FileNotFoundError:
        st.error(f"Não foi possível localizar os arquivos CSV da Lei Paulo Gustavo (`{CSV_MUN_LPG}` ou `{CSV_EST_LPG}`) na raiz do diretório.")
