"""Cliente HTTP para comunicação com a API."""

from typing import Any, Optional

import requests

from config import API_BASE, HEADERS, DEFAULT_TIMEOUT


def api_fetch(endpoint: str, params: Optional[dict] = None) -> Any:
    """
    Realiza uma requisição GET e retorna o JSON da resposta.

    Args:
        endpoint: Endpoint da API (ex.: '/agent/find').
        params: Parâmetros da query string.

    Returns:
        JSON decodificado.
    """
    if params is None:
        params = {}

    url = f"{API_BASE}{endpoint}"
    response = requests.get(
        url,
        params=params,
        headers=HEADERS,
        timeout=DEFAULT_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()