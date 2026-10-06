import pytest

from src.data import quality_interim
from src.data.quality_raw import validate_raw_tables
from src.data.quality_processed import validate_processed_tables
from src.data.quality_interim import (
    validate_interim_tables,
    CONT_PATH,
    INT_PATH,
    REG_PATH,
)


def test_validate_processed_tables_accepts_valid_output(processed_tables_output):
    output_dir = processed_tables_output
    validate_processed_tables(output_dir)


def test_validate_processed_tables_rejects_missing_table(processed_tables_output):
    output_dir = processed_tables_output
    (output_dir / "dim_data.parquet").unlink()

    with pytest.raises(FileNotFoundError, match="Tabelas finais ausentes"):
        validate_processed_tables(output_dir)


def test_validate_interim_tables_accepts_transformed_inputs(
    star_schema_inputs, monkeypatch
):
    monkeypatch.setattr(
        quality_interim, "CONT_PATH", star_schema_inputs["continuity_path"]
    )
    monkeypatch.setattr(
        quality_interim, "INT_PATH", star_schema_inputs["interruptions_path"]
    )
    monkeypatch.setattr(quality_interim, "REG_PATH", star_schema_inputs["region_path"])

    quality_interim.validate_interim_tables()


def test_validate_raw_tables_accepts_complete_inputs(raw_inputs):
    validate_raw_tables(raw_inputs)


def test_validate_raw_tables_rejects_missing_input(raw_inputs):
    (raw_inputs / "raw_interrupcoes_2025.parquet").unlink()

    with pytest.raises(FileNotFoundError, match="Arquivo raw ausente"):
        validate_raw_tables(raw_inputs)
