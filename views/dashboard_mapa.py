import requests
import pandas as pd
import streamlit as st
import plotly.express as px

# Configuração usada quando este painel é executado isoladamente. Na aplicação
# integrada, a configuração global é feita antes de carregar o painel escolhido.
if __name__ == "__main__":
    st.set_page_config(
        page_title="Mapa Cultural do Ceará",
        page_icon="",
        layout="wide"
    )

# config da api
API_BASE = "https://mapacultural.secult.ce.gov.br/api"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json"
}

# Mapeamento oficial de tipos de agentes no Mapas Culturais
TIPOS_AGENTES = {
    1: "Individual",
    2: "Coletivo",
    3: "Empresa"
}

CORES_STATUS = {
    "Aberto": "#2ecc71",
    "Futuro": "#3498db",
    "Encerrado": "#e74c3c",
    "Não publicado": "#95a5a6",
    "Indefinido": "#bdc3c7"
}

session = requests.Session()
session.headers.update(HEADERS)

# funções auxiliares
def tratar_valor(valor):
    """Extrai o ID caso o campo venha como dicionário (relação)."""
    if isinstance(valor, dict):
        return valor.get("id")
    return valor

def converter_data(valor):
    """Converte diferentes formatos de data da API para datetime."""
    if pd.isnull(valor) or valor is None:
        return pd.NaT

    # Algumas versões da API retornam datas como objeto
    if isinstance(valor, dict):
        if "timestamp" in valor:
            try:
                return pd.to_datetime(int(valor["timestamp"]), unit="s")
            except Exception:
                return pd.NaT
        if "date" in valor:
            return pd.to_datetime(valor["date"], errors="coerce")

    # Formato string padrão ou timestamp
    return pd.to_datetime(valor, errors="coerce")

def extrair_area(terms):
    """
    Extrai a primeira área cultural do dicionário de termos.
    Na API do Mapas Culturais, 'terms' é um dict: {"area": ["teatro"], "tag": ["x"]}
    """
    if isinstance(terms, dict):
        areas = terms.get("area", [])
        if isinstance(areas, list) and len(areas) > 0:
            return str(areas[0])
    return "Não informado"

def extrair_lat_lon(location):
    """Extrai latitude e longitude do objeto de localização da API."""
    if isinstance(location, dict):
        lat = location.get("latitude")
        lon = location.get("longitude")
        if lat is not None and lon is not None:
            return pd.Series([float(lat), float(lon)])
    return pd.Series([None, None])

def definir_status_inscricao(row):
    """Define o status real da inscrição com base nas datas."""
    hoje = pd.Timestamp.now()
    inicio = row.get("registrationFrom_dt")
    fim = row.get("registrationTo_dt")
    status = row.get("status")
    
    if status != 1:
        return "Não publicado"
        
    if pd.notnull(inicio) and pd.notnull(fim) and inicio <= hoje <= fim:
        return "Aberto"
        
    if pd.notnull(inicio) and hoje < inicio:
        return "Futuro"
        
    if pd.notnull(fim) and hoje > fim:
        return "Encerrado"
        
    return "Indefinido"

def buscar_dados_paginados(url, params_base):
    """
    Realiza requisições paginadas usando @offset e @limit.
    Garante que todos os dados sejam coletados sem estourar limites da API.
    """
    dados_completos = []
    offset = 0
    limit = params_base.get("@limit", 500)
    
    # Limitar o tamanho do lote para evitar timeout na API
    if limit > 500:
        limit = 500
        params_base["@limit"] = limit
        
    with st.spinner(f"Carregando dados de {url.split('/')[-1]}..."):
        while True:
            params = params_base.copy()
            params["@offset"] = offset
            
            try:
                resposta = session.get(url, params=params, timeout=30)
                resposta.raise_for_status()
                lote = resposta.json()
                
                if not isinstance(lote, list) or len(lote) == 0:
                    break
                    
                dados_completos.extend(lote)
                
                # Se o lote retornado for menor que o limite, chegamos ao fim
                if len(lote) < limit:
                    break
                    
                offset += limit
                
            except Exception as e:
                st.error(f"Erro ao buscar dados (offset {offset}): {e}")
                break
                
    return dados_completos

# carregamento de dados com cache
@st.cache_data(ttl=3600, show_spinner=False)
def carregar_agentes():
    url = f"{API_BASE}/agent/find"
    params = {
        "@select": "id,name,shortDescription,type,status,createTimestamp,location,terms",
        "@limit": 500,
        "@order": "createTimestamp DESC"
    }
    
    dados = buscar_dados_paginados(url, params)
    if not dados:
        return pd.DataFrame()
        
    df = pd.DataFrame(dados)
    
    # tratamento de campos
    df["type"] = df["type"].apply(tratar_valor)
    df["tipo_nome"] = df["type"].map(TIPOS_AGENTES).fillna("Outro")
    
    if "terms" in df.columns:
        df["area"] = df["terms"].apply(extrair_area)
        
    if "location" in df.columns:
        df[["latitude", "longitude"]] = df["location"].apply(extrair_lat_lon)
        
    if "createTimestamp" in df.columns:
        df["createTimestamp_dt"] = df["createTimestamp"].apply(converter_data)
        df["ano_cadastro"] = df["createTimestamp_dt"].dt.year
        
    return df

@st.cache_data(ttl=3600, show_spinner=False)
def carregar_oportunidades():
    url = f"{API_BASE}/opportunity/find"
    params = {
        "@select": "id,name,shortDescription,type,status,createTimestamp,registrationFrom,registrationTo,publishedRegistrations,number,terms",
        "@limit": 500,
        "status": "EQ(1)", # Filtra apenas oportunidades publicadas na própria API
        "@order": "createTimestamp DESC"
    }
    
    dados = buscar_dados_paginados(url, params)
    if not dados:
        return pd.DataFrame()
        
    df = pd.DataFrame(dados)
    
    # tratamento de campos
    df["status"] = df["status"].apply(tratar_valor)
    
    df["registrationFrom_dt"] = df["registrationFrom"].apply(converter_data)
    df["registrationTo_dt"] = df["registrationTo"].apply(converter_data)
    
    df["inscricao_status"] = df.apply(definir_status_inscricao, axis=1)
    
    if "publishedRegistrations" in df.columns:
        df["publishedRegistrations"] = pd.to_numeric(
            df["publishedRegistrations"], errors="coerce"
        ).fillna(0).astype(int)
        
    return df

# interface do dashboard
st.title("Mapa Cultural do Ceará")
st.write("Dashboard analítico com dados reais da API do Mapa Cultural do Ceará.")

# carregar dados
df_agentes = carregar_agentes()
df_oportunidades = carregar_oportunidades()

# métricas gerais
st.subheader("Visão Geral")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total de Agentes", f"{len(df_agentes):,}".replace(",", "."))

with col2:
    st.metric("Total de Oportunidades", f"{len(df_oportunidades):,}".replace(",", "."))

with col3:
    abertas = 0
    if not df_oportunidades.empty:
        abertas = len(df_oportunidades[df_oportunidades["inscricao_status"] == "Aberto"])
    st.metric("Inscrições Abertas", abertas)

with col4:
    total_homologadas = 0
    if not df_oportunidades.empty and "publishedRegistrations" in df_oportunidades.columns:
        total_homologadas = int(df_oportunidades["publishedRegistrations"].sum())
    st.metric("Inscrições Homologadas", f"{total_homologadas:,}".replace(",", "."))

# visualizações principais
tab1, tab2, tab3 = st.tabs([
    "Análise de Agentes",  
    "Oportunidades", 
    "Dados Brutos"
])

# tab 1 - agentes
with tab1:
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.subheader("Tipos de Agentes")
        if not df_agentes.empty and "tipo_nome" in df_agentes.columns:
            tipos = df_agentes["tipo_nome"].value_counts().reset_index()
            tipos.columns = ["Tipo", "Quantidade"]
            
            fig = px.pie(
                tipos, names="Tipo", values="Quantidade", hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig.update_traces(textposition="outside", textinfo="percent+label")
            fig.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)
            
    with col_g2:
        st.subheader("Top 15 Áreas Culturais")
        if not df_agentes.empty and "area" in df_agentes.columns:
            areas = df_agentes["area"].value_counts().head(15).reset_index()
            areas.columns = ["Área Cultural", "Quantidade"]
            
            fig_area = px.bar(
                areas, x="Quantidade", y="Área Cultural", orientation="h",
                color="Quantidade", color_continuous_scale="Viridis"
            )
            fig_area.update_layout(
                showlegend=False, margin=dict(t=20, b=20, l=20, r=20),
                yaxis=dict(categoryorder="total ascending")
            )
            st.plotly_chart(fig_area, use_container_width=True)

    st.subheader("Agentes por Ano de Cadastro")
    if not df_agentes.empty and "ano_cadastro" in df_agentes.columns:
        anos = df_agentes["ano_cadastro"].dropna().astype(int).value_counts().sort_index().reset_index()
        anos.columns = ["Ano", "Quantidade"]
        
        fig2 = px.bar(
            anos, x="Ano", y="Quantidade", text="Quantidade",
            color_discrete_sequence=["#6C63FF"]
        )
        fig2.update_traces(textposition="outside")
        fig2.update_layout(
            xaxis=dict(tickmode="linear", dtick=1),
            margin=dict(t=30, b=20, l=20, r=20),
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig2, use_container_width=True)

# tab 2 - oportunidades
with tab2:
    st.subheader("Status das Oportunidades")
    if not df_oportunidades.empty:
        status = df_oportunidades["inscricao_status"].value_counts().reset_index()
        status.columns = ["Status", "Quantidade"]
        
        ordem = ["Aberto", "Futuro", "Encerrado", "Não publicado", "Indefinido"]
        status["Status"] = pd.Categorical(status["Status"], categories=ordem, ordered=True)
        status = status.sort_values("Status")
        
        fig5 = px.bar(
            status, x="Status", y="Quantidade", text="Quantidade",
            color="Status", color_discrete_map=CORES_STATUS
        )
        fig5.update_traces(textposition="outside")
        fig5.update_layout(
            showlegend=False, margin=dict(t=30, b=20, l=20, r=20),
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig5, use_container_width=True)

    st.subheader("Oportunidades com Inscrições Abertas")
    if not df_oportunidades.empty:
        abertas_df = df_oportunidades[df_oportunidades["inscricao_status"] == "Aberto"].copy()
        
        if not abertas_df.empty:
            for col in ["registrationFrom_dt", "registrationTo_dt"]:
                if col in abertas_df.columns:
                    abertas_df[col] = abertas_df[col].dt.strftime("%d/%m/%Y")
                    
            colunas_exibir = ["name", "registrationFrom_dt", "registrationTo_dt"]
            renomear = {
                "name": "Nome da Oportunidade",
                "registrationFrom_dt": "Início",
                "registrationTo_dt": "Encerramento"
            }
            
            if "publishedRegistrations" in abertas_df.columns:
                colunas_exibir.append("publishedRegistrations")
                renomear["publishedRegistrations"] = "Inscrições Homologadas"
                
            st.dataframe(
                abertas_df[colunas_exibir].rename(columns=renomear),
                use_container_width=True, hide_index=True
            )
        else:
            st.info("Nenhuma oportunidade com inscrições abertas no momento.")

# tab 3 - dados brutos
with tab3:
    st.subheader("Tabela de Agentes Cadastrados")
    if not df_agentes.empty:
        colunas_exibir = ["id", "name", "tipo_nome", "area"]
        renomear = {
            "id": "ID",
            "name": "Nome",
            "tipo_nome": "Tipo",
            "area": "Área Cultural"
        }
        
        st.dataframe(
            df_agentes[colunas_exibir].rename(columns=renomear),
            use_container_width=True, hide_index=True
        )
        
    st.subheader("Tabela de Oportunidades")
    if not df_oportunidades.empty:
        colunas_exibir_opp = ["id", "name", "inscricao_status"]
        renomear_opp = {
            "id": "ID",
            "name": "Nome",
            "inscricao_status": "Status"
        }
        
        if "publishedRegistrations" in df_oportunidades.columns:
            colunas_exibir_opp.append("publishedRegistrations")
            renomear_opp["publishedRegistrations"] = "Inscrições Homologadas"
            
        st.dataframe(
            df_oportunidades[colunas_exibir_opp].rename(columns=renomear_opp),
            use_container_width=True, hide_index=True
        )

# rodape
st.markdown("---")
st.caption("Dados obtidos da API oficial do Mapa Cultural do Ceará.")
