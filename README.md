# Day Trader para Bitcoin

Fork de [Jakeschincariol/day-trader-skill](https://github.com/Jakeschincariol/day-trader-skill), adaptado para pesquisa de **BTC/USDT spot da Binance**. Licenca MIT e autoria original preservadas.

## Uso

Python 3.8+, apenas biblioteca padrao, sem chave API ou acesso a conta.

```sh
python trader-bitcoin/scripts/market.py --interval 5m --out outputs/btc-snapshot.json
python trader-bitcoin/scripts/backtest.py --start 2026-04-23 --end 2026-10-23 --cache work/btc-data --out outputs/btc-analysis
python trader-bitcoin/scripts/backtest.py --self-test
```

O snapshot mostra o ultimo candle fechado, MME 9/21, RSI 14 e ATR 14. Nao transmite em streaming. Intervalos: 1m, 5m, 15m, 1h.

[Grafico no TradingView: BINANCE:BTCUSDT](https://www.tradingview.com/chart/?symbol=BINANCE%3ABTCUSDT)

O backtest usa arquivos oficiais da Binance com SHA256, verifica cobertura minuto a minuto e compara regras fixas sem otimizar parametros. Inclui custos ilustrativos no teste spot, verificacao cronologica e incerteza por reamostragem diaria. Mercado 24/7, datas UTC, fim exclusivo. O proxy de payout fixo e apenas pesquisa direcional: nao reproduz liquidacoes da Ebinex. Resultados historicos e indicadores nao garantem retorno.

## Instalacao como plugin

```text
/plugin marketplace add victordm6/day-trader-skill
/plugin install day-trader-skill@day-trader-skill
```

O plugin registra **12 skills**: o hub `trader-bitcoin` e os **11 adaptadores BTC**. Cada modulo possui `btc.py` como entrada e compartilha o mesmo motor. Os scripts de acoes e suas instrucoes em `references/upstream-SKILL.md` permanecem como legado. [Mapa dos 11 modulos e limites](trader-bitcoin/references/suite.md).

| Modulo | Funcao no Bitcoin |
|---|---|
| trader-scanner | Tendencia, rompimento e volume de BTC em varios intervalos |
| trader-news | Comunicados oficiais Bitcoin Core com deduplicacao |
| trader-entry | Fechamento versus nivel informado |
| trader-exit | Plano spot de entrada, stop e alvo |
| trader-timemachine | Backtest fixo sobre historico Binance 24/7 |
| trader-budget | Dimensionamento fracionado BTC com custos |
| trader-risk | Caixa, risco por operacao/diario e retorno/risco liquido |
| trader-broker | Ticket local em papel, execucao desativada |
| trader-alerts | Observacao de stop/alvo com estado persistente |
| trader-analyst | Retorno, amplitude, volume e volatilidade da amostra |
| trader-pelosi | Registro de divulgacoes BTC com fonte fornecida, sem rastreamento automatico |

```sh
python trader-scanner/btc.py --out outputs/btc-scan.json
python trader-news/btc.py --state outputs/btc-news-state.json --out outputs/btc-news.json
python trader-analyst/btc.py --interval 1h --out outputs/btc-analysis-snapshot.json
```

Na primeira consulta, noticias incluem historico do feed e sao marcadas como backlog, nao como noticias recentes. O feed nao cobre todo o mercado. O modulo Pelosi preserva o nome, mas nao presume compras por congressistas ou identifica baleias. O analista descreve mercado, sem balancos de empresas. O broker nao faz ordens nem simula preenchimentos.

Para Codex, instale as pastas das skills desejadas; nenhuma instalacao global e feita por estes comandos.

## Fluxo integrado de Bitcoin

Entrada por nivel fornecido pelo usuario -> plano spot long com stop/alvo -> tamanho fracionado em BTC -> verificacao de risco -> alertas locais de stop/alvo. Instrucoes e comandos em [workflow](trader-bitcoin/references/workflow.md).

O tamanho respeita caixa, teto por posicao e perda estimada no stop com custos. O risco verifica tambem orcamento diario informado e retorno/risco liquido. Alertas sao persistidos para evitar repeticoes, mas cada chamada faz somente uma checagem; acompanhamento continuo requer agendamento separado. Nenhum modulo envia ordens.

Validacao offline:

```sh
python -m unittest discover -s tests -v
python trader-bitcoin/scripts/backtest.py --self-test
```

## Limites de execucao

Somente leitura e simulacao. Nao envia ordens demo ou reais, nao usa credenciais e nao acessa endpoints privados. Nao inclui futuros, alavancagem, scanner de acoes ou regras de sessao NYSE no fluxo de Bitcoin.

Fontes: [arquivos Binance](https://github.com/binance/binance-public-data), [API publica de mercado](https://developers.binance.com/docs/binance-spot-api-docs/faqs/market_data_only).
