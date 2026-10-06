from pathlib import Path

from src.manifest import build_manifest
from src.package import create_zip_archive
from src.verify import verify_path
from src.signature import ensure_keypair, sign_manifest


def test_verify_fails_for_tampered_zip_artifact(tmp_path):
    run_dir = tmp_path / "run_tampered_zip"
    artifacts_dir = run_dir / "artifacts"
    artifacts_dir.mkdir(parents=True)

    artifact_path = artifacts_dir / "page.html"
    artifact_path.write_text("<html>original</html>", encoding="utf-8")

    capture_metadata = {
        "source_url": "https://example.org",
        "final_url": "https://example.org/",
        "page_title": "Example Domain",
        "http_status": 200,
    }

    build_manifest(run_dir, capture_metadata)
    private_key, _ = ensure_keypair(run_dir / "keys")
    sign_manifest(run_dir / "manifest.json", private_key)

    original_zip = create_zip_archive(run_dir)
    assert original_zip.exists()

    artifact_path.write_text("<html>tampered</html>", encoding="utf-8")

    tampered_zip = create_zip_archive(run_dir, zip_name="tampered_bundle.zip")
    assert tampered_zip.exists()

    result = verify_path(tampered_zip)

    assert result.ok is False
    assert result.checked_files == 1
    assert any("Hash inválido" in error for error in result.errors)
