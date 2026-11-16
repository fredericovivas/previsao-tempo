"""Testes da linha de comandos, sem rede e com funções da API simuladas."""

import io

import pytest

from previsao_tempo import cli
from previsao_tempo.api import (
    APIResponseError,
    CityNotFoundError,
    DailyForecast,
    Location,
    NetworkError,
)
from previsao_tempo.formatting import ATTRIBUTION


LOCATION = Location(
    name="Lisboa",
    country="Portugal",
    admin1="Distrito de Lisboa",
    latitude=38.72,
    longitude=-9.14,
)

DAYS = [
    DailyForecast(
        date="2026-11-16",
        weather_code=2,
        temp_min=12.4,
        temp_max=19.2,
        rain_probability=20,
    ),
    DailyForecast(
        date="2026-11-17",
        weather_code=61,
        temp_min=9.6,
        temp_max=15.4,
        rain_probability=80,
    ),
]


def install_fakes(monkeypatch, calls=None):
    """Substitui as chamadas à API por versões que devolvem dados fixos."""

    def fake_geocode(city, *, timeout):
        if calls is not None:
            calls["geocode"] = (city, timeout)
        return LOCATION

    def fake_forecast(location, *, timeout):
        if calls is not None:
            calls["forecast"] = (location, timeout)
        return DAYS

    monkeypatch.setattr(cli, "geocode_city", fake_geocode)
    monkeypatch.setattr(cli, "fetch_forecast", fake_forecast)


def test_main_with_city_argument_prints_forecast(monkeypatch, capsys):
    install_fakes(monkeypatch)

    assert cli.main(["Lisboa"]) == 0

    captured = capsys.readouterr()
    assert "Previsão do tempo para Lisboa" in captured.out
    assert "chuva 20%" in captured.out
    assert captured.out.splitlines()[-1] == ATTRIBUTION
    assert captured.err == ""


def test_main_passes_timeout_to_api(monkeypatch, capsys):
    calls = {}
    install_fakes(monkeypatch, calls)

    assert cli.main(["--timeout", "2.5", "Lisboa"]) == 0

    assert calls["geocode"] == ("Lisboa", 2.5)
    assert calls["forecast"] == (LOCATION, 2.5)
    assert "Previsão do tempo" in capsys.readouterr().out


def test_main_asks_for_city_when_missing(monkeypatch, capsys):
    prompts = []

    def fake_input(prompt):
        prompts.append(prompt)
        return "Lisboa"

    monkeypatch.setattr("builtins.input", fake_input)
    install_fakes(monkeypatch)

    assert cli.main([]) == 0
    assert prompts == ["Cidade: "]
    assert "Previsão do tempo" in capsys.readouterr().out


def test_main_rejects_empty_city(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda prompt: "   ")

    assert cli.main([]) == 2

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "indica o nome de uma cidade" in captured.err


def test_main_handles_eof(monkeypatch, capsys):
    def raise_eof(prompt):
        raise EOFError

    monkeypatch.setattr("builtins.input", raise_eof)

    assert cli.main([]) == 2
    assert "indica o nome de uma cidade" in capsys.readouterr().err


@pytest.mark.parametrize("value", ["0", "-1", "abc", "nan", "inf"])
def test_timeout_must_be_positive_and_finite(value, capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["--timeout", value, "Lisboa"])

    assert exc.value.code == 2
    assert "timeout" in capsys.readouterr().err.lower()


def test_city_not_found_message(monkeypatch, capsys):
    def fake_geocode(city, *, timeout):
        raise CityNotFoundError(city)

    monkeypatch.setattr(cli, "geocode_city", fake_geocode)

    assert cli.main(["Atlantis"]) == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert 'Cidade não encontrada: "Atlantis".' in captured.err
    assert "Cidade, País" not in captured.err


def test_network_error_message(monkeypatch, capsys):
    def fake_geocode(city, *, timeout):
        raise NetworkError("sem rede")

    monkeypatch.setattr(cli, "geocode_city", fake_geocode)

    assert cli.main(["Lisboa"]) == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Não foi possível contactar a Open-Meteo" in captured.err


def test_api_response_error_message(monkeypatch, capsys):
    def fake_geocode(city, *, timeout):
        raise APIResponseError("resposta inválida")

    monkeypatch.setattr(cli, "geocode_city", fake_geocode)

    assert cli.main(["Lisboa"]) == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "não devolveu uma resposta válida" in captured.err


def test_keyboard_interrupt_returns_130(monkeypatch, capsys):
    def fake_geocode(city, *, timeout):
        raise KeyboardInterrupt

    monkeypatch.setattr(cli, "geocode_city", fake_geocode)

    assert cli.main(["Lisboa"]) == 130

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Operação cancelada" in captured.err


class RecordingStdout(io.StringIO):
    def __init__(self):
        super().__init__()
        self.reconfigure_calls = []

    def reconfigure(self, **kwargs):
        self.reconfigure_calls.append(kwargs)


def test_main_configures_stdout_as_utf8(monkeypatch):
    fake_stdout = RecordingStdout()
    monkeypatch.setattr(cli.sys, "stdout", fake_stdout)
    install_fakes(monkeypatch)

    assert cli.main(["Lisboa"]) == 0

    assert fake_stdout.reconfigure_calls == [
        {"encoding": "utf-8", "errors": "replace"}
    ]
    assert ATTRIBUTION in fake_stdout.getvalue()
