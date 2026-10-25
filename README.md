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

O plugin registra somente `trader-bitcoin`. Os onze modulos de acoes dos EUA permanecem como legado, sem conversao automatica para cripto. Veja [documentacao original](README-upstream.md). Para Codex, instale a pasta `trader-bitcoin` como skill.

## Limites

Somente leitura e simulacao. Nao envia ordens demo ou reais, nao usa credenciais e nao acessa endpoints privados. Nao inclui futuros, alavancagem, scanner de acoes ou regras de sessao NYSE no fluxo de Bitcoin.

Fontes: [arquivos Binance](https://github.com/binance/binance-public-data), [API publica de mercado](https://developers.binance.com/docs/binance-spot-api-docs/faqs/market_data_only).
