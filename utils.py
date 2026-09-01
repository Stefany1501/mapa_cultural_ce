"""Funções utilitárias."""

from typing import Any, Dict, List, Optional

from client import api_fetch


def buscar_todas_paginas(
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    limite_por_pagina: int = 50,
) -> List[dict]:
    """
    Percorre todas as páginas de um endpoint e retorna todos os registros.
    """
    if params is None:
        params = {}

    todos = []
    pagina = 1

    while True:
        resultado = api_fetch(
            endpoint,
            {
                **params,
                "@limit": limite_por_pagina,
                "@page": pagina,
            },
        )

        registros = resultado if isinstance(resultado, list) else []
        todos.extend(registros)

        if len(registros) < limite_por_pagina:
            break

        pagina += 1

    return todos