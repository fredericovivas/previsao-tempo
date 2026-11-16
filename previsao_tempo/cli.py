"""Interface de linha de comandos da previsão do tempo."""

from __future__ import annotations

import argparse
import math
import sys

from .api import (
    APIResponseError,
    CityNotFoundError,
    DEFAULT_TIMEOUT,
    NetworkError,
    fetch_forecast,
    geocode_city,
)
from .formatting import format_forecast


def positive_float(value: str) -> float:
    """Valida o valor de ``--timeout``: tem de ser finito e maior que zero."""
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError(
            "o timeout deve ser um número."
        ) from exc

    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError(
            "o timeout deve ser um número finito maior que zero."
        )

    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mostra a previsão do tempo dos próximos 7 dias.",
    )
    parser.add_argument(
        "cidade",
        nargs="?",
        help="Nome da cidade (ex.: Lisboa).",
    )
    parser.add_argument(
        "--timeout",
        type=positive_float,
        default=DEFAULT_TIMEOUT,
        metavar="SEGUNDOS",
        help="Tempo máximo de espera por pedido, em segundos (por omissão: 10).",
    )
    return parser


def _configure_stdout() -> None:
    """Garante UTF-8 na consola, quando ``reconfigure`` está disponível."""
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, TypeError, ValueError):
            pass


def main(argv: list[str] | None = None) -> int:
    _configure_stdout()
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        city = args.cidade.strip() if args.cidade else ""
        if not city:
            city = input("Cidade: ").strip()
    except EOFError:
        print("Erro: indica o nome de uma cidade.", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nOperação cancelada.", file=sys.stderr)
        return 130

    if not city:
        print("Erro: indica o nome de uma cidade.", file=sys.stderr)
        return 2

    try:
        location = geocode_city(city, timeout=args.timeout)
        days = fetch_forecast(location, timeout=args.timeout)
    except CityNotFoundError:
        print(
            f'Cidade não encontrada: "{city}". Verifica o nome da cidade.',
            file=sys.stderr,
        )
        return 1
    except NetworkError:
        print(
            "Não foi possível contactar a Open-Meteo. "
            "Verifica a ligação à internet ou tenta novamente.",
            file=sys.stderr,
        )
        return 1
    except APIResponseError:
        print(
            "A Open-Meteo não devolveu uma resposta válida. "
            "Tenta novamente mais tarde.",
            file=sys.stderr,
        )
        return 1
    except KeyboardInterrupt:
        print("\nOperação cancelada.", file=sys.stderr)
        return 130

    print(format_forecast(location, days))
    return 0
