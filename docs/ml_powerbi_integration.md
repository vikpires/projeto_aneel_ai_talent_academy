# Integração com Power BI

- A tabela [predicoes_risco.parquet](data\processed\predicoes_risco.parquet) deve ser relacionada à tabela fato: `fato_continuidade.parquet`

- A chave de relacionamento é composta por:

```text
ConjuntoKey
IndicadorKey
Data
```

- No Power BI, crie uma relação usando essas três colunas. Como o Power BI não trabalha bem com chave composta, crie uma coluna concatenada nas duas tabelas:

```text
ChaveContinuidade =
'fato_continuidade'[ConjuntoKey]
    & "|"
    & 'fato_continuidade'[IndicadorKey]
    & "|"
    & FORMAT('fato_continuidade'[Data], "yyyy-MM-dd")
```

- Faça o mesmo em predicoes_risco.

```text
fato_continuidade[ChaveContinuidade]
    1 ──── 1 ou 1 ──── *
predicoes_risco[ChaveContinuidade]

```

- A previsão representa o risco de transgressão do período seguinte, mas está associada às características do período atual (Data). Portanto, não relacione diretamente com fato_causa_mensal.

---

# Medidas DAX para o modelo preditivo de ML

1. Total de Registros

```text
Total de Registros =
COUNTROWS(predicoes_risco)
```

2. Verdadeiros Positivos

```text
Verdadeiros Positivos =
CALCULATE(
    COUNTROWS(predicoes_risco),
    predicoes_risco[predicao_transgressao] = 1,
    predicoes_risco[alvo_real] = 1
)
```

3. Verdadeiros Negativos

```text
Verdadeiros Negativos =
CALCULATE(
    COUNTROWS(predicoes_risco),
    predicoes_risco[predicao_transgressao] = 0,
    predicoes_risco[alvo_real] = 0
)
```

4. Falsos Positivos

```text
Falsos Positivos =
CALCULATE(
    COUNTROWS(predicoes_risco),
    predicoes_risco[predicao_transgressao] = 1,
    predicoes_risco[alvo_real] = 0
)
```

5. Falsos Negativos

```text
Falsos Negativos =
CALCULATE(
    COUNTROWS(predicoes_risco),
    predicoes_risco[predicao_transgressao] = 0,
    predicoes_risco[alvo_real] = 1
)
```

6. Precision

```text
Precision =
DIVIDE(
    [Verdadeiros Positivos],
    [Verdadeiros Positivos] + [Falsos Positivos]
)
```

7. F1 Score

```text
F1 Score =
VAR Precisao = [Precision]
VAR Revocacao = [Recall]
RETURN
    DIVIDE(
        2 * Precisao * Revocacao,
        Precisao + Revocacao
    )
```

8. Recall

```text
Recall =
DIVIDE(
    [Verdadeiros Positivos],
    [Verdadeiros Positivos] + [Falsos Negativos]
)
```

9. ROC-AUC

```text
ROC-AUC =
VAR Base =
    FILTER(
        ALLSELECTED(predicoes_risco),
        NOT ISBLANK(predicoes_risco[score_risco])
            && NOT ISBLANK(predicoes_risco[alvo_real])
    )
VAR Positivos =
    COUNTROWS(
        FILTER(Base, predicoes_risco[alvo_real] = 1)
    )
VAR Negativos =
    COUNTROWS(
        FILTER(Base, predicoes_risco[alvo_real] = 0)
    )
VAR Limiares =
    GENERATESERIES(0, 0.99, 0.01)
VAR AreaROC =
    SUMX(
        Limiares,
        VAR T0 = [Value]
        VAR T1 = T0 + 0.01
        VAR TP0 =
            COUNTROWS(
                FILTER(
                    Base,
                    predicoes_risco[alvo_real] = 1
                        && predicoes_risco[score_risco] >= T0
                )
            )
        VAR FP0 =
            COUNTROWS(
                FILTER(
                    Base,
                    predicoes_risco[alvo_real] = 0
                        && predicoes_risco[score_risco] >= T0
                )
            )
        VAR TP1 =
            COUNTROWS(
                FILTER(
                    Base,
                    predicoes_risco[alvo_real] = 1
                        && predicoes_risco[score_risco] >= T1
                )
            )
        VAR FP1 =
            COUNTROWS(
                FILTER(
                    Base,
                    predicoes_risco[alvo_real] = 0
                        && predicoes_risco[score_risco] >= T1
                )
            )
        VAR TPR0 = DIVIDE(TP0, Positivos, 0)
        VAR FPR0 = DIVIDE(FP0, Negativos, 0)
        VAR TPR1 = DIVIDE(TP1, Positivos, 0)
        VAR FPR1 = DIVIDE(FP1, Negativos, 0)
        RETURN
            DIVIDE(
                ABS(FPR0 - FPR1) * (TPR0 + TPR1),
                2
            )
    )
RETURN
    IF(
        Positivos > 0 && Negativos > 0,
        AreaROC
    )
```

10. PR-AUC

```text
PR-AUC =
VAR Base =
    FILTER(
        ALLSELECTED(predicoes_risco),
        NOT ISBLANK(predicoes_risco[score_risco])
            && NOT ISBLANK(predicoes_risco[alvo_real])
    )
VAR Positivos =
    COUNTROWS(
        FILTER(Base, predicoes_risco[alvo_real] = 1)
    )
VAR Limiares =
    GENERATESERIES(0, 0.99, 0.01)
VAR AreaPR =
    SUMX(
        Limiares,
        VAR T0 = [Value]
        VAR T1 = T0 + 0.01
        VAR TP0 =
            COUNTROWS(
                FILTER(
                    Base,
                    predicoes_risco[alvo_real] = 1
                        && predicoes_risco[score_risco] >= T0
                )
            )
        VAR FP0 =
            COUNTROWS(
                FILTER(
                    Base,
                    predicoes_risco[alvo_real] = 0
                        && predicoes_risco[score_risco] >= T0
                )
            )
        VAR TP1 =
            COUNTROWS(
                FILTER(
                    Base,
                    predicoes_risco[alvo_real] = 1
                        && predicoes_risco[score_risco] >= T1
                )
            )
        VAR FP1 =
            COUNTROWS(
                FILTER(
                    Base,
                    predicoes_risco[alvo_real] = 0
                        && predicoes_risco[score_risco] >= T1
                )
            )
        VAR Recall0 = DIVIDE(TP0, Positivos, 0)
        VAR Recall1 = DIVIDE(TP1, Positivos, 0)
        VAR Precision0 = DIVIDE(TP0, TP0 + FP0, 0)
        VAR Precision1 = DIVIDE(TP1, TP1 + FP1, 0)
        RETURN
            ABS(Recall0 - Recall1)
                * DIVIDE(Precision0 + Precision1, 2)
    )
RETURN
    IF(
        Positivos > 0,
        AreaPR
    )
```
