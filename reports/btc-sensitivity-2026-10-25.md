# Simulacoes exploratorias BTC: 24 variacoes

Periodo: 25/04/2026 a 24/10/2026 UTC; 263.520 candles M1 verificados. Trecho final: 25/08 a 24/10. Toda a janela ja foi examinada; nao e validacao independente.

Grade definida antes desta execucao: taxas de 0, 1, 5 e 10 pontos-base por lado; atraso de entrada de 0 ou 1 barra M5; stop de 1, 2 ou 3 ATR. Fixos: rompimento de 20 barras, volume 1,5x, alvo 2R, prazo maximo de 12 barras apos entrada e slippage adverso de 1 ponto-base por lado. Zero taxa nao significa execucao sem custos.

**Nenhuma das 24 variacoes apresentou media positiva no trecho final.** A configuracao original reproduziu exatamente os resultados anteriores. Nenhuma variante foi promovida a estrategia ativa.

| Taxa por lado (bp) | Atraso M5 | Stop ATR | Operacoes 6m | Media 6m R | Operacoes finais | Media final R | Intervalo final ajustado* |
|---:|---:|---:|---:|---:|---:|---:|---|
| 0 | 0 | 1 | 1142 | -0.2138 | 371 | -0.3064 | [-0.5418, -0.0986] |
| 0 | 0 | 2 | 914 | -0.1089 | 296 | -0.1621 | [-0.3727, 0.0373] |
| 0 | 0 | 3 | 825 | -0.0953 | 271 | -0.1059 | [-0.3180, 0.1028] |
| 0 | 1 | 1 | 1024 | -0.2183 | 333 | -0.1414 | [-0.4220, 0.1275] |
| 0 | 1 | 2 | 871 | -0.0845 | 281 | -0.1381 | [-0.3569, 0.0757] |
| 0 | 1 | 3 | 809 | -0.0623 | 261 | -0.0805 | [-0.2845, 0.1111] |
| 1 | 0 | 1 | 1142 | -0.4308 | 371 | -0.5156 | [-0.7787, -0.2845] |
| 1 | 0 | 2 | 914 | -0.2220 | 296 | -0.2679 | [-0.4839, -0.0560] |
| 1 | 0 | 3 | 825 | -0.1707 | 271 | -0.1769 | [-0.3943, 0.0306] |
| 1 | 1 | 1 | 1024 | -0.4362 | 333 | -0.3499 | [-0.6483, -0.0669] |
| 1 | 1 | 2 | 871 | -0.1961 | 281 | -0.2448 | [-0.4656, -0.0219] |
| 1 | 1 | 3 | 809 | -0.1379 | 261 | -0.1524 | [-0.3570, 0.0470] |
| 5 | 0 | 1 | 1142 | -1.2988 | 371 | -1.3524 | [-1.7960, -0.9757] |
| 5 | 0 | 2 | 914 | -0.6743 | 296 | -0.6907 | [-0.9749, -0.4233] |
| 5 | 0 | 3 | 825 | -0.4726 | 271 | -0.4610 | [-0.7186, -0.2283] |
| 5 | 1 | 1 | 1024 | -1.3079 | 333 | -1.1840 | [-1.6243, -0.8148] |
| 5 | 1 | 2 | 871 | -0.6428 | 281 | -0.6715 | [-0.9586, -0.4079] |
| 5 | 1 | 3 | 809 | -0.4402 | 261 | -0.4400 | [-0.6840, -0.2219] |
| 10 | 0 | 1 | 1142 | -2.3837 | 371 | -2.3984 | [-3.1363, -1.8211] |
| 10 | 0 | 2 | 914 | -1.2397 | 296 | -1.2192 | [-1.6338, -0.8781] |
| 10 | 0 | 3 | 825 | -0.8499 | 271 | -0.8161 | [-1.1285, -0.5391] |
| 10 | 1 | 1 | 1024 | -2.3974 | 333 | -2.2266 | [-2.8802, -1.6996] |
| 10 | 1 | 2 | 871 | -1.2012 | 281 | -1.2050 | [-1.5922, -0.8694] |
| 10 | 1 | 3 | 809 | -0.8180 | 261 | -0.7994 | [-1.1128, -0.5344] |

*10.000 reamostragens de dias por variante, semente 19, caudas ajustadas por Bonferroni para 24 comparacoes e erro familiar nominal de 5%. Intervalos bootstrap aproximados, especialmente nas caudas; nao sao garantia de cobertura nem previsao. Sao 240.000 reamostragens estatisticas, nao novas operacoes de mercado ou amostras independentes.

R e a distancia de preco entre entrada e stop. Ao mudar o stop, muda a unidade R; a tabela nao equivale a uma comparacao de retorno percentual de contas. Os custos sao hipoteses, nao taxas verificadas da conta. Nao houve simulacao de capital, dimensionamento, limites diarios, calendario macro ou ordem real.

O melhor resultado entre os cenarios de taxa zero foi -0,0805R no trecho final, com stop 3 ATR e atraso de uma barra. Seu intervalo ajustado inclui zero; nao demonstra vantagem. Escolher esse resultado depois da comparacao seria selecao exploratoria. Com taxa de 10bp por lado, o melhor do trecho final foi -0,7994R.

[Resultados completos e hashes das fontes](btc-sensitivity-2026-10-25.json)

Reproducao:

```sh
python trader-bitcoin/scripts/sensitivity.py --start 2026-04-25 --end 2026-10-25 --cache work/btc-data --out reports/btc-sensitivity-2026-10-25.json
```
