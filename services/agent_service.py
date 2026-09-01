"""Serviços relacionados aos agentes culturais."""

from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

from client import api_fetch


def buscar_agentes(
    campos: str = "id,name,type,createTimestamp",
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

    return api_fetch("/agent/find", params)



def buscar_agentes_por_tipo(tipo: int, limite: int = 10) -> List[dict]:
    return api_fetch(
        "/agent/find",
        {
            "@select": "id,name,type,shortDescription,createTimestamp",
            "@limit": limite,
            "@order": "createTimestamp DESC",
            "type": f"EQ({tipo})",
            "status": "GTE(0)",
        },
    )



def buscar_agentes_por_nome(nome: str, limite: int = 10) -> List[dict]:
    return api_fetch(
        "/agent/find",
        {
            "@select": "id,name,type,createTimestamp",
            "@limit": limite,
            "@order": "name ASC",
            "name": f"LIKE(*{nome}*)",
            "status": "GTE(0)",
        },
    )



def buscar_agente_por_id(agent_id: int) -> dict:
    return api_fetch(f"/agent/{agent_id}")



def buscar_agentes_por_area(area: str, limite: int = 10) -> List[dict]:
    return api_fetch(
        "/agent/find",
        {
            "@select": "id,name,type,terms,createTimestamp",
            "@limit": limite,
            "@order": "name ASC",
            "status": "GTE(0)",
            "term:area": f"LIKE({area})",
        },
    )

def contar_agentes_por_tipo() -> dict:
    def contar(tipo: int) -> int:
        resultado = api_fetch(
            "/agent/find",
            {
                "@select": "id",
                "@limit": 1,
                "type": f"EQ({tipo})",
                "status": "GTE(0)",
            },
        )
        return len(resultado) if isinstance(resultado, list) else 0

    with ThreadPoolExecutor(max_workers=3) as executor:
        individual = executor.submit(contar, 1).result()
        coletivo = executor.submit(contar, 2).result()
        empresa = executor.submit(contar, 3).result()

    return {
        "individual": individual,
        "coletivo": coletivo,
        "empresa": empresa,
        "total": individual + coletivo + empresa,
    }