from pathlib import Path
import runpy

import streamlit as st


st.set_page_config(
    page_title="Mapa Cultural do Ceará",
    layout="wide",
)

PAGINAS = {
    "Dashboard do Mapa Cultural": "views/dashboard_mapa.py",
    "Análise de Políticas Culturais": "views/analise_politicas.py",
    "Fontes e metodologia": "views/documentacao.py",
}

with st.sidebar:
    st.title("Mapa Cultural do Ceará")
    st.caption("Selecione a área que deseja acessar.")
    pagina = st.radio(
        "Navegação",
        options=list(PAGINAS),
        label_visibility="collapsed",
    )

caminho_pagina = Path(__file__).resolve().parent / PAGINAS[pagina]
runpy.run_path(str(caminho_pagina), run_name=f"painel_{caminho_pagina.stem}")
