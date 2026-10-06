import json
from shutil import copy2

import pytest

from src.hashing import sha256_file
from src.manifest import build_manifest
from src.package import create_zip_archive
from src.signature import ensure_keypair, sign_manifest
from src.verify import verify_path


@pytest.mark.parametrize("as_zip", [False, True])
@pytest.mark.parametrize("mutation", ["remove_signature", "rewrite_then_remove", "invalid_signature", "missing_public_key", "invalid_manifest"])
def test_signed_package_cannot_be_downgraded(tmp_path, as_zip, mutation):
    run = tmp_path / "run"
    (run / "artifacts").mkdir(parents=True)
    artifact = run / "artifacts" / "page.html"
    artifact.write_text("original", encoding="utf-8")
    private, public = ensure_keypair(tmp_path / "private")
    (run / "keys").mkdir()
    copy2(public, run / "keys" / "public_key.pem")
    manifest, manifest_path = build_manifest(run, {"page_title": "synthetic"})
    sign_manifest(manifest_path, private)
    assert verify_path(run).ok

    if mutation == "rewrite_then_remove":
        artifact.write_text("modified", encoding="utf-8")
        for entry in manifest["files"]:
            if entry["path"] == "artifacts/page.html":
                entry["sha256"] = sha256_file(artifact)
                entry["size_bytes"] = artifact.stat().st_size
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    if mutation in {"remove_signature", "rewrite_then_remove"}:
        (run / "manifest.sig").unlink()
    elif mutation == "invalid_signature":
        (run / "manifest.sig").write_text("!invalid-signature!", encoding="utf-8")
    elif mutation == "missing_public_key":
        (run / "keys" / "public_key.pem").unlink()
    elif mutation == "invalid_manifest":
        manifest_path.write_text("{broken-json", encoding="utf-8")

    result = verify_path(create_zip_archive(run) if as_zip else run)
    assert result.ok is False
    assert result.errors
