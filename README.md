# Mapa Cultural do Ceará

Aplicação Streamlit que reúne o dashboard do Mapa Cultural do Ceará, análises de
políticas culturais e a documentação das fontes e metodologias utilizadas.

## Estrutura

- `app.py`: ponto de entrada e navegação lateral.
- `views/`: interfaces dos dashboards e da documentação.
- `data/raw/`: cópias locais, sem transformação, das bases oficiais em XLSX e CSV.
- `requirements.txt`: dependências Python da aplicação.

## Instalação

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Execução

```powershell
streamlit run app.py
```

As origens, os filtros, os tratamentos e as limitações de cada base estão descritos
na opção **Fontes e metodologia** do menu lateral.
