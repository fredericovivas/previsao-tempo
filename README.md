# Previsão do tempo com Open-Meteo

Aplicação de linha de comandos que mostra a previsão dos próximos 7 dias para uma cidade.
Usa a API gratuita Open-Meteo, não precisa de chave de API e apresenta os resultados em português.

## Requisitos

- Python 3 (testado com Python 3.13 no Linux e 3.15 no Windows).
- `requests`, para os pedidos HTTP.
- `pytest`, para os testes.
- Ligação à internet para obter dados reais.
- Não é necessária chave de API.

## Instalação

### Linux e macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### Windows (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Windows (Prompt de Comando)

```bat
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
```

No Windows, se o comando `python` não estiver disponível, podes usar `py -3` no lugar de `python`. Se o PowerShell bloquear a ativação, usa o Prompt de Comando ou consulta a política de execução do PowerShell.

## Utilização

Com a cidade como argumento:

```bash
python -m previsao_tempo Lisboa
```

De forma interativa, sem argumento:

```bash
python -m previsao_tempo
```

O programa pergunta:

```text
Cidade: 
```

Com um tempo máximo de espera diferente do valor por omissão:

```bash
python -m previsao_tempo Lisboa --timeout 20
```

O `--timeout` é o tempo máximo, em segundos, para cada pedido. Por omissão são 10 segundos. O valor tem de ser um número finito maior que zero.

## Exemplo de saída (dados de 16/11/2026)

```text
Previsão do tempo para Lisboa, Distrito de Lisboa, Portugal (7 dias)

segunda-feira, 16/11: mín. 17 °C, máx. 19 °C, chuva 73% — Aguaceiros leves
terça-feira, 17/11: mín. 19 °C, máx. 22 °C, chuva 75% — Chuva leve
quarta-feira, 18/11: mín. 18 °C, máx. 21 °C, chuva 75% — Chuva leve
quinta-feira, 19/11: mín. 12 °C, máx. 18 °C, chuva 40% — Nublado
sexta-feira, 20/11: mín. 12 °C, máx. 16 °C, chuva 31% — Chuva leve
sábado, 21/11: mín. 14 °C, máx. 18 °C, chuva 84% — Aguaceiros leves
domingo, 22/11: mín. 9 °C, máx. 18 °C, chuva 83% — Nublado

Weather data by Open-Meteo.com (https://open-meteo.com/)
```

## Testes

Com a `.venv` ativa:

```bash
python -m pytest
```

Para ver o nome de cada teste:

```bash
python -m pytest -v
```

Os testes usam respostas simuladas, através de `FakeResponse` e `FakeSession`, e o ficheiro `tests/conftest.py` bloqueia a rede ao nível de `socket`, `requests.Session.send` e `requests.get`. Por isso, os testes nunca chamam a API real e não precisam de ligação à internet.

## Como funciona

O programa faz dois pedidos à Open-Meteo:

1. **Geocodificação** — `https://geocoding-api.open-meteo.com/v1/search`
   - Parâmetros usados: `name`, `count=1`, `language=pt` e `format=json`.
   - Devolve o nome, o país, a região administrativa, a latitude e a longitude da cidade.

2. **Previsão** — `https://api.open-meteo.com/v1/forecast`
   - Parâmetros usados: `latitude`, `longitude`, `timezone=auto`, `forecast_days=7` e `daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max`.
   - `timezone=auto` faz com que os dias correspondam ao fuso horário da cidade.

Depois, os códigos WMO são traduzidos para descrições em português e os dados são formatados numa linha por dia. Cada pedido tem 10 segundos de espera máxima por omissão e não há tentativas automáticas.

### Ficheiros do pacote

| Ficheiro | Função |
|---|---|
| `previsao_tempo/__init__.py` | Identifica o pacote e guarda a versão. |
| `previsao_tempo/__main__.py` | Ponto de entrada de `python -m previsao_tempo`. |
| `previsao_tempo/api.py` | Pedidos à Open-Meteo, dataclasses `Location` e `DailyForecast` e exceções de erro. |
| `previsao_tempo/weather.py` | Tradução dos códigos WMO e formatação dos dias da semana. |
| `previsao_tempo/formatting.py` | Construção do texto final e linha de atribuição. |
| `previsao_tempo/cli.py` | Leitura dos argumentos, pergunta da cidade, UTF-8 no `stdout` e tratamento de erros. |
| `tests/conftest.py` | Bloqueia o acesso à rede durante os testes. |
| `tests/test_api.py` | Testes da API com respostas simuladas. |
| `tests/test_cli.py` | Testes da linha de comandos com funções da API simuladas. |
| `tests/test_weather.py` | Testes dos códigos WMO e dos dias da semana. |
| `tests/test_formatting.py` | Testes do texto da previsão e da atribuição. |
| `requirements.txt` | Dependências do projeto. |
| `LICENSE` | Licença MIT do código. |

## Tratamento de erros e códigos de saída

As mensagens de erro são escritas em `stderr`. A previsão normal é escrita em `stdout`.

| Código | Significado |
|---|---|
| `0` | A previsão foi apresentada com sucesso. |
| `1` | Cidade não encontrada, falha de rede ou de tempo de espera, ou resposta inválida da API. |
| `2` | Falta a cidade ou os argumentos são inválidos, incluindo um `--timeout` inválido. |
| `130` | A execução foi interrompida com Ctrl+C. |

Exemplos de mensagens:

- `Cidade não encontrada: "X". Verifica o nome da cidade.`
- `Não foi possível contactar a Open-Meteo. Verifica a ligação à internet ou tenta novamente.`
- `A Open-Meteo não devolveu uma resposta válida. Tenta novamente mais tarde.`

O `--timeout` só aceita números finitos maiores que zero. Valores como `0`, números negativos, `nan` ou `inf` são rejeitados pelo `argparse` com o código de saída `2`.

## Limitações e ideias futuras

- A geocodificação usa `count=1`, ou seja, apenas o primeiro resultado. Nomes ambíguos como `Paris` podem devolver um local que não é o desejado.
- Não há cache: cada execução volta a pedir os dados à API.
- Não há tentativas automáticas (retries): uma falha temporária resulta numa mensagem de erro.
- A previsão é sempre de 7 dias; não há opção para alterar o número de dias.
- O programa apresenta apenas a previsão diária, não a previsão horária.

Ideias futuras, ainda não implementadas:

- Mostrar vários resultados da geocodificação e deixar o utilizador escolher.
- Filtrar a geocodificação por país com o parâmetro `countryCode`.
- Permitir configurar o número de dias.
- Adicionar cache ou tentativas automáticas com limites.

## Atribuição e licenças

A aplicação imprime esta linha no fim de cada previsão:

```text
Weather data by Open-Meteo.com (https://open-meteo.com/)
```

Os dados são disponibilizados pela [Open-Meteo](https://open-meteo.com/) sob a licença [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Os dados foram adaptados: os códigos do tempo foram traduzidos para português e a saída foi reformatada.

Os dados são fornecidos tal como estão, sem garantia de exatidão, disponibilidade ou adequação a um fim específico. Este projeto não é afiliado nem aprovado pela Open-Meteo. O uso da API gratuita da Open-Meteo destina-se a fins não comerciais; confirma as condições atuais. Os termos de uso podem mudar, por isso consulta [https://open-meteo.com/en/terms](https://open-meteo.com/en/terms).

O código deste projeto está sob a licença MIT. Consulta o ficheiro `LICENSE`.
