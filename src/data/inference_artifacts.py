from __future__ import annotations
import logging
from pathlib import Path

import joblib
import pandas as pd

from src.config import PROCESSED_DIR
from src.data.constants import FACT_KEY_COLUMNS

logger = logging.getLogger(__name__)

SRC_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = SRC_DIR.parent
MODEL_DIR = PROJECT_ROOT / "models"
MODEL_PATH = MODEL_DIR / "model_selected.joblib"
METADATA_PATH = MODEL_DIR / "model_metadata.joblib"
MODEL_DATA_DIR = PROCESSED_DIR / "modeling"
PREPARED_INFERENCE_PATH = MODEL_DATA_DIR / "inference_features.parquet"
OUTPUT_PATH = PROCESSED_DIR / "predicoes_risco.parquet"


# Checa se os arquivos obrigatórios existem antes de iniciar a inferência.
def check_required_files() -> None:
    required_files = [
        MODEL_PATH,
        METADATA_PATH,
        PREPARED_INFERENCE_PATH,
    ]

    missing_files = [str(path) for path in required_files if not path.exists()]

    if missing_files:
        raise FileNotFoundError(
            "Arquivos obrigatórios ausentes:\n" + "\n".join(missing_files)
        )


# Carrega o modelo treinado, a lista de features e o limiar operacional a partir dos artefatos salvos.
def load_model_artifacts() -> tuple:
    model_artifact = joblib.load(MODEL_PATH)
    metadata = joblib.load(METADATA_PATH)

    if not isinstance(model_artifact, dict):
        raise TypeError(
            "model_selected.joblib deve conter um dicionário com o modelo treinado."
        )

    model = model_artifact.get("modelo")

    if model is None:
        raise KeyError("A chave 'modelo' não foi encontrada em model_selected.joblib.")

    features_training = model_artifact.get("features") or metadata.get("features_list")

    if not features_training:
        raise KeyError("A lista de features não foi encontrada nos artefatos.")

    threshold = (
        model_artifact.get("limiar_operacional")
        or model_artifact.get("limiar_validacao")
        or metadata.get("limiar_operacional")
    )

    if threshold is None:
        raise KeyError("O limiar operacional não foi encontrado nos artefatos.")

    model_name = (
        model_artifact.get("modelo_selecionado")
        or metadata.get("modelo_selecionado")
        or type(model).__name__
    )

    return (
        model,
        list(features_training),
        float(threshold),
        str(model_name),
    )


# Carrega a base de inferência preparada pelo notebook 04 e valida a integridade das chaves compostas.
def load_prepared_inference_data() -> pd.DataFrame:
    logger.info(
        "Carregando base preparada para inferência: %s",
        PREPARED_INFERENCE_PATH,
    )

    df = pd.read_parquet(PREPARED_INFERENCE_PATH)

    missing_keys = [column for column in FACT_KEY_COLUMNS if column not in df.columns]

    if missing_keys:
        raise KeyError(
            "Chaves ausentes na base de inferência: " + ", ".join(missing_keys)
        )

    if df[FACT_KEY_COLUMNS].isna().any().any():
        raise ValueError("A chave composta contém valores nulos.")

    duplicate_count = int(df.duplicated(subset=FACT_KEY_COLUMNS).sum())

    if duplicate_count:
        raise ValueError(
            "A base possui duplicidades na chave composta: " f"{duplicate_count}"
        )

    return df
