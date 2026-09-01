from services.site_service import get_versao
from services.agent_service import (
    buscar_agentes,
    buscar_agentes_por_tipo,
    buscar_agentes_por_nome,
    buscar_agentes_por_area,
    buscar_agente_por_id,
    contar_agentes_por_tipo,
)
from services.opportunity_service import (
    buscar_editais_publicados,
    buscar_editais_com_inscricoes_abertas,
    contar_editais_por_status,
)
from utils import buscar_todas_paginas


if __name__ == "__main__":
    
    # 1. Versão da API
    versao = get_versao()
    print("Versão:", versao.get("version"))

    # 2. Contagem de agentes por tipo
    print("Agentes por tipo:", contar_agentes_por_tipo())

    # 3. Últimos agentes
    recentes = buscar_agentes(limite=10)
    print("Agentes recentes:", len(recentes))

    # 4. Agentes individuais
    print("Individuais:", len(buscar_agentes_por_tipo(1, limite=20)))

    # 5. Busca por nome
    print(
        'Agentes com "teatro":',
        len(buscar_agentes_por_nome("teatro", limite=20)),
    )

    # 6. Busca por área cultural
    print("Músicos:", len(buscar_agentes_por_area("Música", limite=20)))

    # 7. Detalhes do primeiro agente retornado
    print("\nBuscando um agente válido por ID...")

    agentes = buscar_agentes(
        campos="id,name",
        limite=20,
        filtros={"status": "GTE(0)"},
    )

    agente_valido = None

    for item in agentes:
        agent_id = item.get("id")

        try:
            agente = buscar_agente_por_id(agent_id)
            if agente:
                agente_valido = agente
                print(f"Agente #{agent_id}: {agente.get('name')}")
                break
        except Exception:
            # Ignora IDs que retornam 404
            continue

    if agente_valido is None:
        print("Nenhum agente válido encontrado.")

    # 8. Editais publicados
    print(
        "\nEditais publicados:",
        len(buscar_editais_publicados(limite=20)),
    )

    # 9. Editais com inscrições abertas
    print(
        "Com inscrições abertas:",
        len(buscar_editais_com_inscricoes_abertas(limite=10)),
    )

    # 10. Contagem de editais por status
    print("Editais por status:", contar_editais_por_status())

    # 11. Todas as páginas
    todos_coletivos = buscar_todas_paginas(
        "/agent/find",
        {
            "@select": "id,name",
            "type": "EQ(2)",
            "status": "GTE(0)",
        },
    )
    print("Total real de coletivos:", len(todos_coletivos))