"""Tradução dos códigos WMO e formatação dos dias da semana."""

from __future__ import annotations

from datetime import date

# Códigos WMO usados pela Open-Meteo, traduzidos para português.
WMO_DESCRIPTIONS: dict[int, str] = {
    0: "Céu limpo",
    1: "Predominantemente limpo",
    2: "Parcialmente nublado",
    3: "Nublado",
    45: "Nevoeiro",
    48: "Nevoeiro com geada",
    51: "Chuvisco leve",
    53: "Chuvisco moderado",
    55: "Chuvisco forte",
    56: "Chuvisco gelado leve",
    57: "Chuvisco gelado forte",
    61: "Chuva leve",
    63: "Chuva moderada",
    65: "Chuva forte",
    66: "Chuva gelada leve",
    67: "Chuva gelada forte",
    71: "Neve leve",
    73: "Neve moderada",
    75: "Neve forte",
    77: "Grãos de neve",
    80: "Aguaceiros leves",
    81: "Aguaceiros moderados",
    82: "Aguaceiros fortes",
    85: "Aguaceiros de neve leves",
    86: "Aguaceiros de neve fortes",
    95: "Trovoada",
    96: "Trovoada com granizo leve",
    99: "Trovoada com granizo forte",
}

WEEKDAYS: tuple[str, ...] = (
    "segunda-feira",
    "terça-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sábado",
    "domingo",
)

UNKNOWN_DESCRIPTION = "Condições desconhecidas"


def describe_weather(code: int | None) -> str:
    """Devolve uma descrição simples em português para um código WMO."""
    if code is None:
        return UNKNOWN_DESCRIPTION
    return WMO_DESCRIPTIONS.get(code, UNKNOWN_DESCRIPTION)


def format_day(iso_date: str) -> str:
    """Converte ``2026-11-16`` em ``segunda-feira, 16/11``.

    Se a data não for válida, devolve o texto original para não interromper
    a apresentação da previsão.
    """
    try:
        day = date.fromisoformat(iso_date)
    except (TypeError, ValueError):
        return iso_date

    return f"{WEEKDAYS[day.weekday()]}, {day.day:02d}/{day.month:02d}"
