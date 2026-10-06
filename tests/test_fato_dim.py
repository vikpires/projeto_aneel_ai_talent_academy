import json
import duckdb

import src.data.fato_dim as fato_dim


# Testes para a função run_fato_dim do módulo fato_dim, que constrói o esquema estrela a partir de arquivos intermediários.
def test_run_fato_dim_builds_star_schema_from_interim_files(
    star_schema_inputs, monkeypatch
):
    monkeypatch.setattr(fato_dim, "CONT_PATH", star_schema_inputs["continuity_path"])
    monkeypatch.setattr(fato_dim, "INT_PATH", star_schema_inputs["interruptions_path"])
    monkeypatch.setattr(fato_dim, "LIM_PATH", star_schema_inputs["limits_path"])
    monkeypatch.setattr(fato_dim, "ATR_PATH", star_schema_inputs["attributes_path"])
    monkeypatch.setattr(fato_dim, "REG_PATH", star_schema_inputs["region_path"])

    fato_dim.run_fato_dim(
        input_dir=star_schema_inputs["input_dir"],
        output_dir=star_schema_inputs["output_dir"],
        ano_inicio=2021,
        ano_fim=2021,
    )

    expected_tables = {
        f"{table_name}.parquet" for table_name in fato_dim.PIPELINE_TABLES
    }
    output_dir = star_schema_inputs["output_dir"]
    assert {path.name for path in output_dir.glob("*.parquet")} == expected_tables

    manifest = json.loads((output_dir / "_manifesto.json").read_text())
    assert manifest["status"] == "SUCCESS"
    assert manifest["total_tabelas"] == len(expected_tables)

    result = duckdb.sql(
        f"SELECT COUNT(*) AS total FROM read_parquet('{output_dir / 'fato_continuidade.parquet'}')"
    ).fetchone()
    assert result == (1,)

    fact_columns = {
        row[0]
        for row in duckdb.sql(
            f"DESCRIBE SELECT * FROM read_parquet('{output_dir / 'fato_causa_mensal.parquet'}')"
        ).fetchall()
    }
    assert {
        "DataKey",
        "ConjuntoKey",
        "CausaKey",
        "NivelTensao",
        "QtdInterrupcoes",
        "DuracaoTotalHoras",
        "DuracaoMediaHoras",
        "MaiorInterrupcaoHoras",
        "ContribDEC_Estimada",
        "ContribFEC_Estimada",
    } <= fact_columns

    fato_dim.run_fato_dim(
        input_dir=star_schema_inputs["input_dir"],
        output_dir=output_dir,
        ano_inicio=2021,
        ano_fim=2021,
        force_rebuild=True,
    )


# Testa se a função run_fato_dim lança um erro quando os arquivos de entrada intermediários estão ausentes.
def test_run_fato_dim_rejects_missing_inputs(tmp_path):
    import pytest

    with pytest.raises(FileNotFoundError, match="Arquivos ausentes"):
        fato_dim.run_fato_dim(
            input_dir=tmp_path / "interim",
            output_dir=tmp_path / "processed",
            ano_inicio=2021,
            ano_fim=2021,
        )
