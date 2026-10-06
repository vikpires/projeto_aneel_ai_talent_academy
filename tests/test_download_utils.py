import pytest

from src.utils import download_utils
from tests.constants import PROCESSED_ARCHIVE_NAME


# Testes para a função download_and_extract do módulo download_utils
def test_download_and_extract_zip(monkeypatch, tmp_path, zip_response_factory):
    response = zip_response_factory({"dim_data.parquet": b"parquet"})
    monkeypatch.setattr(
        download_utils.requests, "get", lambda *args, **kwargs: response
    )

    extracted = download_utils.download_and_extract(
        "https://example.test/release",
        PROCESSED_ARCHIVE_NAME,
        tmp_path / "processed",
    )

    assert extracted == [tmp_path / "processed" / "dim_data.parquet"]
    assert extracted[0].read_bytes() == b"parquet"


# Testa se a função download_and_extract rejeita arquivos ZIP que tentam explorar vulnerabilidades de caminho (zip slip).
def test_download_and_extract_rejects_zip_slip(
    monkeypatch, tmp_path, zip_response_factory
):
    response = zip_response_factory({"../outside.txt": b"unsafe"})
    monkeypatch.setattr(
        download_utils.requests, "get", lambda *args, **kwargs: response
    )

    with pytest.raises(ValueError, match="Caminho inseguro"):
        download_utils.download_and_extract(
            "https://example.test/release",
            PROCESSED_ARCHIVE_NAME,
            tmp_path / "processed",
        )

    assert not (tmp_path / "outside.txt").exists()
