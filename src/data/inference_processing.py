from __future__ import annotations
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from src.data.constants import FACT_KEY_COLUMNS
from src.data.inference_artifacts import (
    load_model_artifacts,
)

logger = logging.getLogger(__name__)


# Prepara a base de inferência para o modelo, garantindo que todas as features necessárias estejam presentes e na ordem correta.
def prepare_model_input(
    df: pd.DataFrame,
    features_training: list[str],
) -> pd.DataFrame:
    missing_features = [
        feature for feature in features_training if feature not in df.columns
    ]

    if missing_features:
        raise ValueError(
            "A base preparada para inferência não possui todas as "
            "features utilizadas no treinamento.\n"
            f"Quantidade ausente: {len(missing_features)}\n"
            f"Exemplos: {missing_features[:20]}"
        )

    X_input = df.loc[:, features_training].copy()

    if list(X_input.columns) != features_training:
        raise ValueError(
            "A ordem das features da inferência difere da ordem "
            "utilizada no treinamento."
        )

    if X_input.isna().any().any():
        null_columns = X_input.columns[X_input.isna().any()].tolist()

        raise ValueError(
            "Existem valores nulos nas features de inferência: " f"{null_columns[:20]}"
        )

    return X_input


# Prepara a base de inferência para o modelo, garantindo que todas as features necessárias estejam presentes e na ordem correta.
def prepare_inference_features(
    df: pd.DataFrame,
    features_training: list[str] | None = None,
) -> pd.DataFrame:
    if features_training is None:
        _, features_training, _, _ = load_model_artifacts()

    return prepare_model_input(
        df=df,
        features_training=features_training,
    )


# Executa a inferência de risco utilizando o modelo treinado e retorna os scores de risco.
def get_risk_scores(
    model,
    X_input: pd.DataFrame,
) -> np.ndarray:
    if not hasattr(model, "predict_proba"):
        raise TypeError("O modelo selecionado não possui predict_proba.")

    scores = model.predict_proba(X_input)[:, 1]

    if not np.isfinite(scores).all():
        raise ValueError("O modelo gerou scores inválidos.")

    return scores


# Valida se o DataFrame de saída possui as colunas obrigatórias e se a coluna 'alvo_real' contém apenas 0 ou 1.
def validate_output_schema(df: pd.DataFrame) -> None:
    required_columns = [
        *FACT_KEY_COLUMNS,
        "alvo_real",
        "score_risco",
        "predicao_transgressao",
        "zona_risco",
        "acao_recomendada",
    ]

    missing_columns = [
        column for column in required_columns if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Colunas obrigatórias ausentes no resultado: " + ", ".join(missing_columns)
        )

    if not df["alvo_real"].isin([0, 1]).all():
        raise ValueError("A coluna 'alvo_real' deve conter apenas 0 ou 1.")
