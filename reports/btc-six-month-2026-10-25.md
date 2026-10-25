# Backtest BTCUSDT: seis meses completos

Periodo UTC: 25/04/2026 inclusive a 25/10/2026 exclusivo (ultimo dia: 24/10). Binance spot; 183 dias, 263.520 candles M1, sem lacunas. 35 arquivos diarios/mensais com SHA256 verificado. Parametros fixos, sem otimizacao nesta rodada.

## Regra principal de compra spot

M5: fechamento acima da maxima das 20 barras anteriores; volume >= 1,5x media anterior; entrada na abertura seguinte; stop de 1 ATR14, alvo 2R, encerramento em ate 12 barras. Uma posicao por vez. Stop prevalece em toques intrabar ambiguos; gaps usam abertura. Custos ilustrativos: taxa de 10bp e slippage de 1bp por lado.

| Periodo | Operacoes | Positivas apos custos | Media liquida | Fator de lucro | Drawdown em R |
|---|---:|---:|---:|---:|---:|
| Seis meses | 1142 | 17.34% | -2.3837R | 0.0497 | 2722.21R |
| Trecho final: 25/08 a 24/10 | 371 | 17.79% | -2.3984R | 0.0481 | 891.72R |

Media bruta antes de taxas e slippage de saida: -0.1053R; ja incorpora slippage de entrada. R corresponde a distancia de preco entre entrada e stop. Custos podem exceder 1R quando o stop e estreito. Somatorios de R nao sao retorno percentual nem simulacao de uma conta com capital, tamanhos variaveis ou limite diario.

Intervalo bootstrap diario de 95% da media no trecho final: [-2.8518, -2.0013] R/operacao (10.000 reamostragens, semente 19). Nao e previsao.

## Estabilidade mensal da regra spot

| Mes UTC de entrada | Operacoes | Media liquida R |
|---|---:|---:|
| 2026-04 | 41 | -2.2577 |
| 2026-05 | 193 | -2.2320 |
| 2026-06 | 155 | -1.3972 |
| 2026-07 | 204 | -2.1476 |
| 2026-08 | 220 | -3.3308 |
| 2026-09 | 194 | -2.1583 |
| 2026-10 | 135 | -2.9091 |

Abril e outubro sao meses parciais.

## Comparacoes direcionais M1

Estes testes sao proxies com aposta fixa de 1 unidade, payout hipotetico de 90% e empate devolvido. Nao sao compras spot nem reproduzem precos, strikes ou liquidacoes da Ebinex. Nao comparar suas unidades diretamente com R do spot.

| Proxy | Operacoes | Media por aposta | Media no trecho final |
|---|---:|---:|---:|
| MME9/21 + RSI14, proxima abertura | 229741 | -0.060223 unidade | -0.048989 unidade |
| Mesma regra, atraso de uma barra | 119836 | -0.061614 unidade | -0.055757 unidade |

## Movimento do BTC e limites

BTC iniciou em 77437.13 e encerrou em 80888.16 USDT: variacao de 4.46% antes de custos. Maximo drawdown entre fechamentos M1: 30.12%. Essa variacao do ativo nao e resultado da estrategia.

Conclusao: a regra spot nao passou nos criterios historicos e permanece sem suporte para candidatos de compra. Ambos os proxies M1 tambem tiveram media negativa. Parte substancial do periodo ja foi examinada: o trecho final e uma separacao cronologica, nao um teste inteiramente independente. Nao foram adicionados filtros depois de olhar o resultado.

O calendario Investing nao foi incluido no backtest: nao ha historico versionado dos eventos como eram conhecidos em cada instante. Noticias, execucao real, livro de ofertas, impostos, minimos de ordem, tamanhos de conta e latencia real nao foram simulados. Custos sao hipoteses fixas, nao taxas verificadas da conta. Nenhuma ordem foi enviada.

[Resultados e hashes](btc-six-month-results-2026-10-25.json) | [Evidencia da regra](btc-breakout-evidence-2026-10-25.json) | [Fonte Binance](https://github.com/binance/binance-public-data)

Reproducao:

```sh
python trader-bitcoin/scripts/backtest.py --start 2026-04-25 --end 2026-10-25 --cache work/btc-data --out outputs/backtest-2026-10-25
```
