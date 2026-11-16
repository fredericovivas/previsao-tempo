"""Testes da tradução dos códigos WMO e dos dias da semana."""

import pytest

from previsao_tempo.weather import (
    UNKNOWN_DESCRIPTION,
    WMO_DESCRIPTIONS,
    describe_weather,
    format_day,
)


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        (0, "Céu limpo"),
        (1, "Predominantemente limpo"),
        (2, "Parcialmente nublado"),
        (3, "Nublado"),
        (45, "Nevoeiro"),
        (48, "Nevoeiro com geada"),
        (51, "Chuvisco leve"),
        (53, "Chuvisco moderado"),
        (55, "Chuvisco forte"),
        (56, "Chuvisco gelado leve"),
        (57, "Chuvisco gelado forte"),
        (61, "Chuva leve"),
        (63, "Chuva moderada"),
        (65, "Chuva forte"),
        (66, "Chuva gelada leve"),
        (67, "Chuva gelada forte"),
        (71, "Neve leve"),
        (73, "Neve moderada"),
        (75, "Neve forte"),
        (77, "Grãos de neve"),
        (80, "Aguaceiros leves"),
        (81, "Aguaceiros moderados"),
        (82, "Aguaceiros fortes"),
        (85, "Aguaceiros de neve leves"),
        (86, "Aguaceiros de neve fortes"),
        (95, "Trovoada"),
        (96, "Trovoada com granizo leve"),
        (99, "Trovoada com granizo forte"),
        (123, UNKNOWN_DESCRIPTION),
        (None, UNKNOWN_DESCRIPTION),
    ],
)
def test_describe_weather(code, expected):
    assert describe_weather(code) == expected


def test_all_required_wmo_codes_are_present():
    required = {
        0,
        1,
        2,
        3,
        45,
        48,
        51,
        53,
        55,
        56,
        57,
        61,
        63,
        65,
        66,
        67,
        71,
        73,
        75,
        77,
        80,
        81,
        82,
        85,
        86,
        95,
        96,
        99,
    }
    assert required <= WMO_DESCRIPTIONS.keys()


@pytest.mark.parametrize(
    ("iso_date", "expected"),
    [
        ("2026-11-16", "segunda-feira, 16/11"),
        ("2026-11-17", "terça-feira, 17/11"),
        ("2026-11-18", "quarta-feira, 18/11"),
        ("2026-11-19", "quinta-feira, 19/11"),
        ("2026-11-20", "sexta-feira, 20/11"),
        ("2026-11-21", "sábado, 21/11"),
        ("2026-11-22", "domingo, 22/11"),
        ("2026-01-01", "quinta-feira, 01/01"),
    ],
)
def test_format_day(iso_date, expected):
    assert format_day(iso_date) == expected


@pytest.mark.parametrize("invalid", ["", "2026-13-01", "ontem", None])
def test_format_day_invalid_returns_input(invalid):
    assert format_day(invalid) == invalid
