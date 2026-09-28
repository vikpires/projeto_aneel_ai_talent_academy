from __future__ import annotations
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from src.data.constants import CONTEXT_COLUMNS
from src.data.inference_artifacts import (
    OUTPUT_PATH,
    check_required_files,
    load_model_artifacts,
    load_prepared_inference_data,
)
from src.data.inference_processing import (
    prepare_model_input,
    get_risk_scores,
    validate_output_schema,
)

logger = logging.getLogger(__name__)


# Executa a inferência de risco utilizando o modelo treinado e salva os resultados em um arquivo Parquet.
def run_risk_inference(
    output_path: Path = OUTPUT_PATH,
) -> pd.DataFrame:
    check_required_files()

    model, features_training, threshold, model_name = load_model_artifacts()

    df_prepared = load_prepared_inference_data()
    X_input = prepare_model_input(
        df=df_prepared,
        features_training=features_training,
    )

    logger.info(
        "Executando inferência com o modelo: %s",
        model_name,
    )

    scores = get_risk_scores(model, X_input)
    predictions = (scores >= threshold).astype("int8")

    # Mantém as colunas dimensionais disponíveis.
    output_columns = [
        column for column in CONTEXT_COLUMNS if column in df_prepared.columns
    ]

    df_result = df_prepared[output_columns].copy()

    df_result["score_risco"] = np.round(scores, 8)
    df_result["predicao_transgressao"] = predictions
    df_result["limiar_operacional"] = threshold
    df_result["modelo"] = model_name

    df_result["zona_risco"] = np.select(
        [
            scores < threshold * 0.5,
            scores < threshold,
            scores >= threshold,
        ],
        [
            "Verde - Baixo Risco",
            "Amarela - Risco Moderado",
            "Vermelha - Alto Risco",
        ],
        default="Indefinido",
    )

    df_result["acao_recomendada"] = np.select(
        [
            scores < threshold * 0.5,
            scores < threshold,
            scores >= threshold,
        ],
        [
            "Acompanhamento de rotina",
            "Revisão complementar",
            "Auditoria manual prioritária",
        ],
        default="Revisar registro",
    )

    validate_output_schema(df_result)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_result.to_parquet(output_path, index=False)

    logger.info(
        "Parquet gerado: %s",
        output_path.resolve(),
    )
    logger.info(
        "Registros processados: %s",
        f"{len(df_result):,}",
    )

    return df_result


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    result = run_risk_inference()

    print("\n--- Inferência concluída ---")
    print(f"Registros: {len(result):,}")
    print(f"Arquivo: {OUTPUT_PATH}")
    print("\nDistribuição das zonas:")
    print(result["zona_risco"].value_counts())
