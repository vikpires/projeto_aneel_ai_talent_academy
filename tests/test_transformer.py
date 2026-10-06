from datetime import datetime

from src.data.transformer import transform_data
from src.data.constants import ANO_INICIO, ANO_FIM
from tests.constants import (
    QUERY_INPUT_CONTINUIDADE,
    QUERY_INPUT_INTERRUPCOES,
    QUERY_OUTPUT_CONTINUIDADE,
    QUERY_OUTPUT_INTERRUPCOES,
)


# Testa se a função transform_data cria corretamente os arquivos Parquet esperados a partir dos dados de entrada.
def test_execute_continuidade_transformation_creates_expected_parquet(
    tmp_path, db_connection
):
    raw_path = tmp_path / "raw.parquet"
    output_path = tmp_path / "output.parquet"
    db_connection.sql(QUERY_INPUT_CONTINUIDADE).write_parquet(str(raw_path))
    transform_data(
        db_connection,
        "filter_continuidade",
        raw_path,
        output_path,
        ano_inicio=ANO_INICIO,
        ano_fim=ANO_FIM,
    )

    result = db_connection.sql(
        QUERY_OUTPUT_CONTINUIDADE.format(raw_path=output_path)
    ).fetchall()
    assert result == [(2021, 1, "X", "12345678000199", 10, "CONJUNTO", "DEC", 1.5)]


# Testa se a função transform_data cria corretamente os arquivos Parquet esperados a partir dos dados de entrada de interrupções.
def test_execute_interrupcoes_transformation_creates_expected_parquet(
    tmp_path, db_connection
):
    raw_path = tmp_path / "raw_interrupcoes.parquet"
    output_path = tmp_path / "output_interrupcoes.parquet"
    db_connection.sql(QUERY_INPUT_INTERRUPCOES).write_parquet(str(raw_path))

    transform_data(
        db_connection,
        "filter_interrupcoes",
        raw_path,
        output_path,
        ano_inicio=ANO_INICIO,
        ano_fim=ANO_FIM,
    )

    result = db_connection.sql(
        QUERY_OUTPUT_INTERRUPCOES.format(raw_path=output_path)
    ).fetchall()
    assert result == [
        (
            2021,
            5,
            datetime(2021, 5, 10, 10, 0),
            datetime(2021, 5, 10, 11, 30),
            1.5,
            "X",
            "12345678000199",
            20,
            "99",
            15,
            100,
            13.8,
            "Programada",
            7,
            "Manutencao",
        )
    ]


# Testa se a função transform_data retorna o mesmo arquivo Parquet existente quando não há necessidade de reconstrução (force=False).
def test_transform_data_skips_valid_interim_cache(tmp_path, db_connection):
    raw_path = tmp_path / "raw.parquet"
    output_path = tmp_path / "output.parquet"
    db_connection.sql(QUERY_INPUT_CONTINUIDADE).write_parquet(str(raw_path))
    output_path.write_bytes(b"existing parquet")

    transform_data(
        db_connection,
        "filter_continuidade",
        raw_path,
        output_path,
        ano_inicio=ANO_INICIO,
        ano_fim=ANO_FIM,
    )

    assert output_path.read_bytes() == b"existing parquet"


# Testa se a função transform_data força a reconstrução do arquivo Parquet mesmo quando um cache válido já existe (force=True).
def test_transform_data_force_rebuilds_interim_cache(tmp_path, db_connection):
    raw_path = tmp_path / "raw.parquet"
    output_path = tmp_path / "output.parquet"
    db_connection.sql(QUERY_INPUT_CONTINUIDADE).write_parquet(str(raw_path))
    output_path.write_bytes(b"existing parquet")

    transform_data(
        db_connection,
        "filter_continuidade",
        raw_path,
        output_path,
        force=True,
        ano_inicio=ANO_INICIO,
        ano_fim=ANO_FIM,
    )

    assert output_path.read_bytes() != b"existing parquet"


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
