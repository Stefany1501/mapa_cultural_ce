import streamlit as st


st.title("Fontes e metodologia")
st.write(
    "Esta página documenta a origem, a forma de obtenção, os tratamentos e os "
    "limites de cada conjunto de dados exibido no painel."
)

st.info(
    "Os panoramas nacionais mostram as bases de origem antes de qualquer recorte. "
    "As abas ‘Ceará + Mapa’ aplicam o filtro territorial e, quando há uma chave "
    "compatível, relacionam esses registros aos dados do Mapa Cultural do Ceará."
)

with st.expander("Mapa Cultural do Ceará", expanded=True):
    st.markdown(
        """
**Fonte:** [API do Mapa Cultural do Ceará](https://mapacultural.secult.ce.gov.br/api/)

**Forma de obtenção:** requisições HTTP à API pública, com paginação por `@limit` e
`@offset`. São consultadas as entidades de agentes, oportunidades, espaços, eventos
e projetos. As respostas JSON são transformadas em tabelas.

**Tratamentos:** conversão de datas; classificação dos tipos de agente e do status
das inscrições; extração de área cultural, município e coordenadas quando presentes;
e cálculo de contagens e séries por ano. O cache é renovado a cada 60 minutos.

**Abrangência:** a própria plataforma é estadual. Os totais representam os registros
publicados/retornados pela API no momento da consulta, não um censo de toda a
atividade cultural cearense.
        """
    )

with st.expander("Lei Rouanet (SALIC)"):
    st.markdown(
        """
**Fonte institucional:** [Incentivos da Lei Rouanet — Portal de Dados da Cultura](https://dados.cultura.gov.br/dataset/incentivos-da-lei-rouanet)

**Forma de obtenção:** API pública do SALIC (`api.salic.cultura.gov.br/api/v1/projetos`),
consultada em lotes paginados. O ano escolhido é enviado como filtro à API.

**Panorama Brasil:** não aplica filtro de UF nem cruza registros com o Mapa Cultural.
Apresenta quantidade de projetos, valores aprovado e captado e distribuição pela UF
de origem do proponente.

**Ceará + Mapa:** envia `uf=CE` à API SALIC. O cruzamento é nominal: nomes de
proponentes e agentes são convertidos para minúsculas, têm acentos, pontuação e
palavras conectivas removidos, e somente chaves normalizadas exatamente iguais são
consideradas correspondências.

**Limites:** igualdade de nomes não comprova identidade jurídica; homônimos podem
gerar falso positivo e grafias diferentes podem gerar falso negativo. Os valores são
os declarados pelo SALIC para o período consultado.
        """
    )

with st.expander("Política Nacional Aldir Blanc (PNAB)"):
    st.markdown(
        """
**Fonte institucional:** [Implementação e Execução da PNAB — Portal de Dados da Cultura](https://dados.cultura.gov.br/dataset/implementacao-e-execucao-da-politica-nacional-aldir-blanc-de-fomento-a-cultura-pnab)

**Forma de obtenção:** planilha XLSX de adesão, armazenada localmente como
`data/raw/pnab/adesao_aldir.xlsx`. A leitura começa no cabeçalho da planilha oficial e descarta a
linha auxiliar imediatamente posterior. As colunas são padronizadas e valores e
população são convertidos para tipos numéricos.

**Panorama Brasil:** inclui estados e municípios de todas as UFs presentes no arquivo,
sem integração com o Mapa Cultural.

**Ceará + Mapa:** filtra `UF do Ente = CE`. Para municípios, normaliza o nome do ente
e o município informado pelo agente no Mapa Cultural, agregando a quantidade de
agentes cadastrados em cada correspondência territorial.

**Limites:** o vínculo territorial não afirma que o agente recebeu recursos da PNAB;
ele apenas contextualiza os recursos do ente com os cadastros existentes no Mapa.
Registros sem município preenchido ou com nomes incompatíveis permanecem com zero.
        """
    )

with st.expander("Lei Paulo Gustavo (LPG)"):
    st.markdown(
        """
**Fonte institucional:** [Implementação e Execução da LPG — Portal de Dados da Cultura](https://dados.cultura.gov.br/dataset/implementacao-e-execucao-da-lei-paulo-gustavo-lpg)

**Forma de obtenção:** dois CSV oficiais de adesão, um municipal
(`data/raw/lpg/adesao_municipios.csv`) e um estadual
(`data/raw/lpg/adesao_estados.csv`). Os campos de valor
disponível são convertidos para números antes das agregações.

**Panorama Brasil:** usa integralmente os dois CSV, sem filtro estadual e sem
cruzamento, apresentando cobertura e recursos por UF.

**Ceará + Mapa:** filtra `UF = CE` no arquivo municipal e `Estado = CEARA` no arquivo
estadual. O cruzamento municipal segue a mesma normalização territorial usada na
PNAB e contabiliza agentes do Mapa por município.

**Limites:** o cruzamento é contextual, não identifica beneficiários individuais.
Os indicadores refletem os arquivos locais e só mudam quando esses arquivos são
substituídos por versões mais recentes da fonte.
        """
    )

st.subheader("Regras gerais de leitura")
st.markdown(
    """
- **Antes do cruzamento:** visão nacional e integral da base selecionada.
- **Após o cruzamento:** recorte exclusivo do Ceará e integração compatível com a
  granularidade da fonte.
- Ausência de correspondência significa apenas que a chave adotada não encontrou um
  registro compatível; não significa ausência de atuação, adesão ou recebimento.
- APIs podem mudar entre execuções. XLSX e CSV representam a versão dos arquivos
  atualmente armazenados junto à aplicação.
    """
)
