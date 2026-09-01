"""Serviços relacionados a editais e oportunidades."""

from concurrent.futures import ThreadPoolExecutor
from datetime import date
from typing import Dict, List, Optional

from client import api_fetch



def buscar_editais(
    campos: str = (
        "id,name,shortDescription,registrationFrom,"
        "registrationTo,status,type"
    ),
    limite: int = 10,
    pagina: int = 1,
    ordem: str = "createTimestamp DESC",
    filtros: Optional[Dict[str, str]] = None,
) -> List[dict]:
    if filtros is None:
        filtros = {}

    params = {
        "@select": campos,
        "@limit": limite,
        "@page": pagina,
        "@order": ordem,
        **filtros,
    }

    return api_fetch("/opportunity/find", params)



def buscar_editais_publicados(limite: int = 10) -> List[dict]:
    return api_fetch(
        "/opportunity/find",
        {
            "@select": (
                "id,name,shortDescription,"
                "registrationFrom,registrationTo,type"
            ),
            "@limit": limite,
            "@order": "registrationTo ASC",
            "status": "EQ(1)",
        },
    )



def buscar_editais_com_inscricoes_abertas(limite: int = 10) -> List[dict]:
    hoje = date.today().isoformat()

    return api_fetch(
        "/opportunity/find",
        {
            "@select": (
                "id,name,shortDescription,"
                "registrationFrom,registrationTo,type"
            ),
            "@limit": limite,
            "@order": "registrationTo ASC",
            "status": "EQ(1)",
            "registrationFrom": f"LTE({hoje})",
            "registrationTo": f"GTE({hoje})",
        },
    )



def buscar_editais_por_nome(nome: str, limite: int = 10) -> List[dict]:
    return api_fetch(
        "/opportunity/find",
        {
            "@select": (
                "id,name,shortDescription,"
                "registrationFrom,registrationTo,status"
            ),
            "@limit": limite,
            "@order": "name ASC",
            "name": f"LIKE(*{nome}*)",
            "status": "GTE(0)",
        },
    )



def buscar_edital_por_id(opportunity_id: int) -> dict:
    return api_fetch(f"/opportunity/{opportunity_id}")



def contar_editais_por_status() -> dict:
    def contar(status: int) -> int:
        resultado = api_fetch(
            "/opportunity/find",
            {
                "@select": "id",
                "@limit": 1,
                "status": f"EQ({status})",
            },
        )
        return len(resultado) if isinstance(resultado, list) else 0

    with ThreadPoolExecutor(max_workers=2) as executor:
        publicados = executor.submit(contar, 1).result()
        rascunhos = executor.submit(contar, 0).result()

    return {
        "publicados": publicados,
        "rascunhos": rascunhos,
        "total": publicados + rascunhos,
    }