"""Testes da API, sempre com respostas simuladas e sem rede."""

import copy

import pytest
import requests

from previsao_tempo.api import (
    APIResponseError,
    CityNotFoundError,
    DEFAULT_TIMEOUT,
    FORECAST_URL,
    GEOCODING_URL,
    DailyForecast,
    Location,
    NetworkError,
    fetch_forecast,
    geocode_city,
)


class FakeResponse:
    """Resposta HTTP falsa, suficiente para o código da API."""

    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


class FakeSession:
    """Sessão falsa: devolve respostas preparadas e regista as chamadas."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        if not self.responses:
            raise AssertionError("Pedido inesperado")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


LOCATION = Location(
    name="Lisboa",
    country="Portugal",
    admin1="Distrito de Lisboa",
    latitude=38.72,
    longitude=-9.14,
)

GEOCODING_PAYLOAD = {
    "results": [
        {
            "name": "Lisboa",
            "country": "Portugal",
            "admin1": "Distrito de Lisboa",
            "latitude": 38.72,
            "longitude": -9.14,
        }
    ]
}

FORECAST_PAYLOAD = {
    "daily": {
        "time": [f"2026-11-{day:02d}" for day in range(16, 23)],
        "weather_code": [0, 1, 2, 3, 61, 80, 95],
        "temperature_2m_max": [19.2, 18.4, 17.6, 16.8, 15.2, 14.4, 13.6],
        "temperature_2m_min": [12.4, 11.6, 10.8, 10.0, 9.2, 8.4, 7.6],
        "precipitation_probability_max": [0, 10, 20, 30, 80, 60, None],
    }
}


def test_geocode_city_returns_location():
    session = FakeSession(FakeResponse(GEOCODING_PAYLOAD))

    location = geocode_city("Lisboa", session=session)

    assert location == LOCATION
    assert session.calls == [
        {
            "url": GEOCODING_URL,
            "params": {
                "name": "Lisboa",
                "count": 1,
                "language": "pt",
                "format": "json",
            },
            "timeout": DEFAULT_TIMEOUT,
        }
    ]


@pytest.mark.parametrize("payload", [{"results": []}, {}])
def test_geocode_city_without_results_raises(payload):
    session = FakeSession(FakeResponse(payload))

    with pytest.raises(CityNotFoundError):
        geocode_city("Atlantis", session=session)


@pytest.mark.parametrize(
    "error",
    [
        requests.Timeout("demorou"),
        requests.ConnectionError("sem rede"),
        requests.RequestException("outra falha"),
    ],
)
def test_geocode_city_network_errors_raise_network_error(error):
    with pytest.raises(NetworkError):
        geocode_city("Lisboa", session=FakeSession(error))


def test_geocode_city_http_error_raises_api_response_error():
    session = FakeSession(FakeResponse({}, status_code=500))

    with pytest.raises(APIResponseError):
        geocode_city("Lisboa", session=session)


def test_geocode_city_invalid_json_raises_api_response_error():
    session = FakeSession(FakeResponse(ValueError("json inválido")))

    with pytest.raises(APIResponseError):
        geocode_city("Lisboa", session=session)


def test_geocode_city_incomplete_data_raises_api_response_error():
    session = FakeSession(FakeResponse({"results": [{"name": "Lisboa"}]}))

    with pytest.raises(APIResponseError):
        geocode_city("Lisboa", session=session)


def test_fetch_forecast_parses_days():
    session = FakeSession(FakeResponse(FORECAST_PAYLOAD))

    days = fetch_forecast(LOCATION, session=session)

    assert len(days) == 7
    assert days[0] == DailyForecast(
        date="2026-11-16",
        weather_code=0,
        temp_min=12.4,
        temp_max=19.2,
        rain_probability=0.0,
    )
    assert days[-1] == DailyForecast(
        date="2026-11-22",
        weather_code=95,
        temp_min=7.6,
        temp_max=13.6,
        rain_probability=None,
    )
    assert session.calls == [
        {
            "url": FORECAST_URL,
            "params": {
                "latitude": 38.72,
                "longitude": -9.14,
                "daily": (
                    "weather_code,"
                    "temperature_2m_max,"
                    "temperature_2m_min,"
                    "precipitation_probability_max"
                ),
                "timezone": "auto",
                "forecast_days": 7,
            },
            "timeout": DEFAULT_TIMEOUT,
        }
    ]


def test_fetch_forecast_respects_days_limit():
    session = FakeSession(FakeResponse(FORECAST_PAYLOAD))

    days = fetch_forecast(LOCATION, session=session, days=2)

    assert len(days) == 2
    assert session.calls[0]["params"]["forecast_days"] == 2


@pytest.mark.parametrize("payload", [{}, {"daily": None}])
def test_fetch_forecast_without_daily_raises(payload):
    with pytest.raises(APIResponseError):
        fetch_forecast(LOCATION, session=FakeSession(FakeResponse(payload)))


def test_fetch_forecast_missing_field_raises():
    payload = copy.deepcopy(FORECAST_PAYLOAD)
    del payload["daily"]["weather_code"]

    with pytest.raises(APIResponseError):
        fetch_forecast(LOCATION, session=FakeSession(FakeResponse(payload)))


def test_fetch_forecast_mismatched_lengths_raises():
    payload = copy.deepcopy(FORECAST_PAYLOAD)
    payload["daily"]["time"] = payload["daily"]["time"][:-1]

    with pytest.raises(APIResponseError):
        fetch_forecast(LOCATION, session=FakeSession(FakeResponse(payload)))


def test_fetch_forecast_empty_arrays_raises():
    payload = {
        "daily": {
            "time": [],
            "weather_code": [],
            "temperature_2m_max": [],
            "temperature_2m_min": [],
            "precipitation_probability_max": [],
        }
    }

    with pytest.raises(APIResponseError):
        fetch_forecast(LOCATION, session=FakeSession(FakeResponse(payload)))


def test_fetch_forecast_invalid_value_raises():
    payload = copy.deepcopy(FORECAST_PAYLOAD)
    payload["daily"]["temperature_2m_max"][0] = "muito quente"

    with pytest.raises(APIResponseError):
        fetch_forecast(LOCATION, session=FakeSession(FakeResponse(payload)))


def test_fetch_forecast_network_error():
    with pytest.raises(NetworkError):
        fetch_forecast(
            LOCATION,
            session=FakeSession(requests.Timeout("demorou")),
        )
