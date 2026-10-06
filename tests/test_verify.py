from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from src.hashing import sha256_file
from src.verify import verify_run_directory
from src.signature import ensure_keypair, sign_manifest


class TestVerify(unittest.TestCase):
    def test_verify_succeeds_when_files_are_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            artifacts = run_dir / "artifacts"
            artifacts.mkdir()

            file_path = artifacts / "page.html"
            file_path.write_text("<html>ok</html>", encoding="utf-8")

            manifest = {
                "files": [
                    {
                        "path": "artifacts/page.html",
                        "sha256": sha256_file(file_path),
                        "size_bytes": file_path.stat().st_size,
                    }
                ]
            }
            (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            private_key, _ = ensure_keypair(run_dir / "keys")
            sign_manifest(run_dir / "manifest.json", private_key)

            result = verify_run_directory(run_dir)
            self.assertTrue(result.ok)
            self.assertEqual(result.checked_files, 1)
            self.assertEqual(result.errors, [])

    def test_verify_fails_when_file_is_tampered(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            artifacts = run_dir / "artifacts"
            artifacts.mkdir()

            file_path = artifacts / "page.html"
            file_path.write_text("<html>ok</html>", encoding="utf-8")

            manifest = {
                "files": [
                    {
                        "path": "artifacts/page.html",
                        "sha256": sha256_file(file_path),
                        "size_bytes": file_path.stat().st_size,
                    }
                ]
            }
            (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            private_key, _ = ensure_keypair(run_dir / "keys")
            sign_manifest(run_dir / "manifest.json", private_key)

            file_path.write_text("<html>alterado</html>", encoding="utf-8")

            result = verify_run_directory(run_dir)
            self.assertFalse(result.ok)
            self.assertEqual(result.checked_files, 1)
            self.assertTrue(any("Hash inválido" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()
