"""Configuração comum dos testes: bloqueia qualquer acesso real à rede."""

import socket

import pytest
import requests


def _blocked(*args, **kwargs):
    raise RuntimeError("Acesso à rede bloqueado nos testes")


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    """Impede pedidos reais, mesmo que o código use ``requests.Session``."""
    monkeypatch.setattr(socket.socket, "connect", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)
    monkeypatch.setattr(requests.Session, "send", _blocked)
    monkeypatch.setattr(requests, "get", _blocked)
    yield
