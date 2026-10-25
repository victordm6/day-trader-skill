# Ebinex: pesquisa de operacoes com payout fixo

Este modo le arquivos locais de observacao e comprovantes. Nao conecta contas,
nao captura cookies, nao envia ordens e nao gera sinais de entrada validados.
Os 11 adaptadores aceitam `--venue ebinex`; sem essa opcao permanece o fluxo spot.

## Contrato separado

Na consulta visual de 25/10/2026 havia Bitcoin/BTCUSDX, conta demo, M1,
valor preparado de US$1 e payout anunciado de 90%. Sao observacoes pontuais,
nao configuracoes universais da plataforma. Nao registrar saldo ou identidade
do usuario em fixtures publicas. O arquivo de exemplo abaixo e sintetico.

BTCUSDT da Binance nao e uma fonte de strikes/liquidacoes BTCUSDX. A Regra 14410
spot, de 25h36, permanece incompatível com a janela M1 observada. Alterar prazo,
indicadores ou agenda cria outra estrategia, com nova identificacao e validacao.

Payout e lucro/stake: 0.90 significa lucro de 90%, credito total de 1.90 vezes
o stake quando ha ganho. Perda custa o stake inteiro, mais taxas informadas.
Com payout 90%, sem taxas nem empates, o equilibrio teorico e 52.63% de ganhos.
Nao e uma probabilidade estimada. Nao importar ATR/stop/alvo ou tamanho em BTC
para dimensionar uma opcao. Empate exige regra explicitamente documentada.

## Observacao local

```sh
python trader-entry/btc.py --venue ebinex --observation observacao.json --out outputs/ebinex-check.json
python trader-risk/btc.py --venue ebinex --observation observacao.json --cash 100 --max-loss 1 --daily-limit 3 --daily-used 0 --fees 0 --out outputs/ebinex-risk.json
python trader-broker/btc.py --venue ebinex --observation observacao.json --out outputs/ebinex-disabled.json
```

Os limites numericos sao demonstracoes, nao recomendacoes. Observacoes vencem
apos 90 segundos. Datas futuras, conta real, fonte Binance, instrumento ou prazo
divergente bloqueiam o perfil de pesquisa demo M1. OBSERVED_ONLY apenas confirma
a consistencia do arquivo, nao verifica independentemente sua autenticidade.
Valor preparado nao comprova investimento. Entry/exit produzem WAIT; broker
produz EXECUTION_DISABLED em qualquer estado. Risco nunca autoriza ordens.

## Contabilidade de resultados confirmados

```sh
python trader-analyst/btc.py --venue ebinex --observation observacao.json --ledger comprovantes.json --initial-balance 100 --out outputs/ebinex-results.json
python trader-timemachine/btc.py --venue ebinex --observation observacao.json --ledger comprovantes.json --initial-balance 100 --out outputs/ebinex-audit.json
```

O documento do ledger tem `mode`, `coverage_complete`, `coverage_evidence` e
`trades`. Cada registro fechado exige id unico, mode, symbol=BTCUSDX,
product=digital_fixed_payout, direction=BUY/SELL, entry_utc, expiry_utc,
settled_utc, stake_usdt, payout_ratio, fees_usdt, cash_return_usdt,
status=WIN/LOSS/TIE, confirmation=explicit_platform_result e result_evidence.
TIE exige tie_rule=refund/loss. Campos financeiros sao valores em USDT.
IDs e evidencias de exemplo nunca sao operacoes reais. Taxas ausentes nao viram zero.

PENDING/OPEN/UNCERTAIN nao entram nas perdas nem nos ganhos. Debito isolado,
marcador de grafico ou saldo nao confirma resultado. Rejeitar duplicatas,
mistura de contas/instrumentos, horarios inconsistentes e creditos contraditorios.
Nao incluir depositos/saques no array. `coverage_complete` e declaracao da fonte,
nao certificacao do programa. Sem cobertura completa ou com pendencias, somente
subtotal observado e taxa de acerto da amostra encerrada; lucro completo fica null.
Saldo por P&L fechado nao representa caixa disponivel ou patrimonio com posicoes
abertas. Drawdown deste modo usa apenas encerramentos, nao marcas intradiarias.

Timemachine neste modo audita os resultados fornecidos; nao e backtest de precos.
Faltam historicos da Ebinex com strikes, vencimentos, payouts e liquidacoes para
testar uma estrategia. Um proxy Binance deve continuar identificado como proxy.
Preservar uma janela ainda nao usada antes de pesquisar novas regras.

## Papel dos modulos

| Modulo | Modo Ebinex |
|---|---|
| scanner | Confere observacao, instrumento, prazo e payout; nao consulta Binance |
| news | Contexto fornecido; sem feed de noticias Ebinex ou sinal automatico |
| entry | WAIT ate existir estrategia Ebinex validada; nunca traduz compra spot |
| exit | Le estado e resultados; nao transforma stop/alvo spot em vencimento |
| timemachine | Auditoria de ledger explicito; sem dados retorna WAIT_FOR_EBINEX_SETTLEMENT_DATA |
| budget | Stake inteiro mais taxas versus limites pessoais informados |
| risk | Recalcula caixa e orcamento de perda por operacao/diario |
| broker | Execucao desativada, inclusive demo |
| alerts | Checagem unica de observacao fornecida; sem monitor automatico |
| analyst | Resultados confirmados, cobertura e pendencias do ledger |
| pelosi | Sem rastreamento de divulgacoes aplicavel a opcoes Ebinex |

## Fontes e limites verificados

- Interface existente: https://app.ebinex.com/traderoom (consulta visual, 25/10/2026).
- Produtos, payout predefinido e latencia descrita pela empresa:
  https://blog.ebinex.com/como-funcionam-os-ativos-na-ebinex-explicacao-simples-e-direta/
- Guia oficial e politica contra automacao destinada a operar na plataforma:
  https://blog.ebinex.com/como-funciona-a-ebinex-guia-completo-da-plataforma/

As paginas publicas nao confirmam cada especificacao contratual. Fonte de
liquidacao, regra de strike, empate, taxas e latencia efetiva permanecem
desconhecidos ate evidencia especifica. Nenhuma promessa de rentabilidade.
