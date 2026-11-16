"""Construção do texto da previsão em português."""

from __future__ import annotations

from typing import Protocol, Sequence

from .weather import describe_weather, format_day

ATTRIBUTION = "Weather data by Open-Meteo.com (https://open-meteo.com/)"


class LocationLike(Protocol):
    """Dados mínimos de uma localização usados na formatação."""

    name: str
    admin1: str | None
    country: str


class DailyForecastLike(Protocol):
    """Dados mínimos de um dia de previsão usados na formatação."""

    date: str
    weather_code: int
    temp_min: float
    temp_max: float
    rain_probability: float | None


def location_label(location: LocationLike) -> str:
    """Monta o nome da localização sem repetir a região administrativa."""
    parts = [location.name]

    admin1 = getattr(location, "admin1", None)
    country = getattr(location, "country", "")

    if admin1 and admin1 != location.name:
        parts.append(admin1)
    if country:
        parts.append(country)

    return ", ".join(parts)


def _format_temperature(value: float) -> str:
    # round() devolve um inteiro, evitando o "-0 °C" que o formato ".0f"
    # produz com valores como -0,4.
    return f"{round(value)} °C"


def _format_rain(probability: float | None) -> str:
    if probability is None:
        return "n/d"
    return f"{probability:.0f}%"


def format_forecast(
    location: LocationLike,
    days: Sequence[DailyForecastLike],
) -> str:
    """Devolve a previsão completa, terminando com a atribuição da Open-Meteo."""
    parts = [
        f"Previsão do tempo para {location_label(location)} ({len(days)} dias)"
    ]

    if days:
        parts.append("")
        for day in days:
            parts.append(
                f"{format_day(day.date)}: "
                f"mín. {_format_temperature(day.temp_min)}, "
                f"máx. {_format_temperature(day.temp_max)}, "
                f"chuva {_format_rain(day.rain_probability)} — "
                f"{describe_weather(day.weather_code)}"
            )

    parts.append("")
    parts.append(ATTRIBUTION)
    return "\n".join(parts)
