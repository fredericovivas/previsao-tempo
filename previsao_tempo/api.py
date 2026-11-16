"""Acesso à API Open-Meteo: geocodificação e previsão diária."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
DEFAULT_TIMEOUT = 10.0

DAILY_VARIABLES = (
    "weather_code,"
    "temperature_2m_max,"
    "temperature_2m_min,"
    "precipitation_probability_max"
)
DAILY_FIELDS = (
    "time",
    "weather_code",
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_probability_max",
)


@dataclass(frozen=True)
class Location:
    """Cidade encontrada pela geocodificação."""

    name: str
    country: str
    admin1: str | None
    latitude: float
    longitude: float


@dataclass(frozen=True)
class DailyForecast:
    """Previsão resumida de um dia."""

    date: str
    weather_code: int
    temp_min: float
    temp_max: float
    rain_probability: float | None


class WeatherError(Exception):
    """Erro base para problemas ao obter a previsão."""


class CityNotFoundError(WeatherError):
    """A geocodificação não encontrou a cidade."""


class NetworkError(WeatherError):
    """Não foi possível comunicar com a API."""


class APIResponseError(WeatherError):
    """A API respondeu, mas com dados inválidos ou um estado de erro."""


def _get_json(
    url: str,
    params: Mapping[str, object],
    *,
    session: requests.Session | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict:
    """Faz um pedido e devolve o JSON, traduzindo falhas para exceções próprias."""
    getter = session.get if session is not None else requests.get

    try:
        response = getter(url, params=params, timeout=timeout)
    except requests.Timeout as exc:
        raise NetworkError(
            "O pedido à Open-Meteo demorou demasiado tempo."
        ) from exc
    except requests.ConnectionError as exc:
        raise NetworkError(
            "Não foi possível ligar à Open-Meteo."
        ) from exc
    except requests.RequestException as exc:
        raise NetworkError(
            "Ocorreu uma falha de rede ao contactar a Open-Meteo."
        ) from exc

    if response.status_code != 200:
        raise APIResponseError(
            f"A Open-Meteo respondeu com o estado HTTP {response.status_code}."
        )

    try:
        data = response.json()
    except ValueError as exc:
        raise APIResponseError(
            "A Open-Meteo devolveu uma resposta que não é JSON válido."
        ) from exc

    if not isinstance(data, dict):
        raise APIResponseError(
            "A Open-Meteo devolveu uma resposta com um formato inesperado."
        )

    return data


def geocode_city(
    city: str,
    *,
    session: requests.Session | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> Location:
    """Obtém as coordenadas de uma cidade através da API de geocodificação."""
    params = {
        "name": city,
        "count": 1,
        "language": "pt",
        "format": "json",
    }
    data = _get_json(GEOCODING_URL, params, session=session, timeout=timeout)

    results = data.get("results")
    if not isinstance(results, list) or not results:
        raise CityNotFoundError(f'Cidade não encontrada: "{city}".')

    first = results[0]
    if not isinstance(first, dict):
        raise APIResponseError("A geocodificação devolveu dados inválidos.")

    try:
        admin1_value = first.get("admin1")
        return Location(
            name=str(first["name"]),
            country=str(first.get("country", "")),
            admin1=None if admin1_value is None else str(admin1_value),
            latitude=float(first["latitude"]),
            longitude=float(first["longitude"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise APIResponseError(
            "A geocodificação devolveu dados incompletos."
        ) from exc


def fetch_forecast(
    location: Location,
    *,
    session: requests.Session | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    days: int = 7,
) -> list[DailyForecast]:
    """Obtém a previsão diária para uma localização."""
    params = {
        "latitude": location.latitude,
        "longitude": location.longitude,
        "daily": DAILY_VARIABLES,
        "timezone": "auto",
        "forecast_days": days,
    }
    data = _get_json(FORECAST_URL, params, session=session, timeout=timeout)

    daily = data.get("daily")
    if not isinstance(daily, dict):
        raise APIResponseError("A previsão veio sem o bloco de dados diários.")

    missing = [field for field in DAILY_FIELDS if field not in daily]
    if missing:
        raise APIResponseError(
            "A previsão veio sem estes campos: " + ", ".join(missing) + "."
        )

    arrays = {field: daily[field] for field in DAILY_FIELDS}
    if not all(isinstance(values, list) for values in arrays.values()):
        raise APIResponseError("A previsão veio com dados diários inválidos.")

    length = len(arrays["time"])
    if length == 0:
        raise APIResponseError("A previsão veio sem dias.")
    if any(len(values) != length for values in arrays.values()):
        raise APIResponseError(
            "A previsão veio com listas de tamanhos diferentes."
        )

    forecasts: list[DailyForecast] = []
    for index in range(length):
        try:
            rain = arrays["precipitation_probability_max"][index]
            forecasts.append(
                DailyForecast(
                    date=str(arrays["time"][index]),
                    weather_code=int(arrays["weather_code"][index]),
                    temp_min=float(arrays["temperature_2m_min"][index]),
                    temp_max=float(arrays["temperature_2m_max"][index]),
                    rain_probability=None if rain is None else float(rain),
                )
            )
        except (TypeError, ValueError) as exc:
            raise APIResponseError(
                "A previsão veio com valores inválidos."
            ) from exc

    return forecasts[:days]
