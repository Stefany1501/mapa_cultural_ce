"""Serviços relacionados ao site."""

from client import api_fetch


def get_versao() -> dict:
    """Retorna a versão da instalação do Mapa Cultural."""
    return api_fetch("/site/version")