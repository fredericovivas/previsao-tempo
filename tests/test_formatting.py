"""Testes da construção do texto da previsão."""

from types import SimpleNamespace

from previsao_tempo.formatting import (
    ATTRIBUTION,
    format_forecast,
    location_label,
)


def make_location(name="Lisboa", admin1=None, country="Portugal"):
    return SimpleNamespace(name=name, admin1=admin1, country=country)


def make_day(
    date="2026-11-16",
    weather_code=2,
    temp_min=12.4,
    temp_max=19.2,
    rain_probability=20,
):
    return SimpleNamespace(
        date=date,
        weather_code=weather_code,
        temp_min=temp_min,
        temp_max=temp_max,
        rain_probability=rain_probability,
    )


def test_location_label_without_admin1():
    assert location_label(make_location()) == "Lisboa, Portugal"


def test_location_label_does_not_repeat_admin1():
    location = make_location(name="Lisboa", admin1="Lisboa")
    assert location_label(location) == "Lisboa, Portugal"


def test_location_label_includes_different_admin1():
    location = make_location(name="Paris", admin1="Texas", country="United States")
    assert location_label(location) == "Paris, Texas, United States"


def test_location_label_without_country():
    assert location_label(make_location(name="Lisboa", country="")) == "Lisboa"


def test_format_forecast_contains_all_fields():
    days = [
        make_day(
            date="2026-11-16",
            weather_code=2,
            temp_min=12.4,
            temp_max=19.2,
            rain_probability=20,
        ),
        make_day(
            date="2026-11-17",
            weather_code=61,
            temp_min=9.6,
            temp_max=15.4,
            rain_probability=80,
        ),
    ]

    output = format_forecast(make_location(), days)

    assert "Previsão do tempo para Lisboa, Portugal (2 dias)" in output
    assert (
        "segunda-feira, 16/11: mín. 12 °C, máx. 19 °C, chuva 20% — "
        "Parcialmente nublado"
    ) in output
    assert (
        "terça-feira, 17/11: mín. 10 °C, máx. 15 °C, chuva 80% — Chuva leve"
    ) in output
    assert output.splitlines()[-1] == ATTRIBUTION


def test_format_forecast_missing_rain_probability():
    output = format_forecast(make_location(), [make_day(rain_probability=None)])
    assert "chuva n/d" in output


def test_format_forecast_unknown_weather_code():
    output = format_forecast(make_location(), [make_day(weather_code=123)])
    assert "Condições desconhecidas" in output


def test_format_forecast_empty_days():
    output = format_forecast(make_location(), [])

    assert output.splitlines()[0] == (
        "Previsão do tempo para Lisboa, Portugal (0 dias)"
    )
    assert output.splitlines()[-1] == ATTRIBUTION


def test_attribution_text_is_exact():
    assert ATTRIBUTION == "Weather data by Open-Meteo.com (https://open-meteo.com/)"


def test_format_forecast_never_shows_negative_zero():
    for value in (-0.4, -0.5, -0.0):
        output = format_forecast(
            make_location(),
            [make_day(temp_min=value, temp_max=value)],
        )

        assert "mín. 0 °C, máx. 0 °C" in output
        assert "-0 °C" not in output


def test_format_forecast_keeps_negative_temperatures():
    output = format_forecast(
        make_location(),
        [make_day(temp_min=-1.4, temp_max=-0.4)],
    )

    assert "mín. -1 °C" in output
    assert "máx. 0 °C" in output
    assert "-0 °C" not in output
