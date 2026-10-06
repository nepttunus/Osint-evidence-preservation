from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

from .hashing import sha256_file
from .signature import verify_manifest_signature


@dataclass
class VerifyResult:
    ok: bool
    checked_files: int
    errors: list[str]


def verify_run_directory(run_dir: Path) -> VerifyResult:
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        return VerifyResult(False, 0, ["Manifest não encontrado"])

    errors: list[str] = []
    checked_files = 0

    # Evidence packages are signed. A missing signature must never downgrade
    # authentication to a hash-only check of attacker-controlled reference data.
    signature_path = run_dir / "manifest.sig"
    public_key_path = run_dir / "keys" / "public_key.pem"
    if not signature_path.is_file():
        return VerifyResult(False, 0, ["Assinatura do manifesto em falta"])
    if not public_key_path.is_file():
        return VerifyResult(False, 0, ["Chave pública em falta para validar assinatura"])
    try:
        signature_valid = verify_manifest_signature(manifest_path, signature_path, public_key_path)
    except Exception:
        signature_valid = False
    if not signature_valid:
        errors.append("Assinatura do manifesto inválida")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError, OSError):
        return VerifyResult(False, 0, errors + ["Manifesto ilegível ou JSON inválido"])
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
        return VerifyResult(False, 0, errors + ["Inventário do manifesto inválido"])

    for entry in manifest.get("files", []):
        file_path = run_dir / entry["path"]
        if not file_path.exists():
            errors.append(f"Ficheiro em falta: {entry['path']}")
            continue

        current_hash = sha256_file(file_path)
        if current_hash != entry["sha256"]:
            errors.append(f"Hash inválido: {entry['path']}")
        checked_files += 1

    return VerifyResult(len(errors) == 0, checked_files, errors)


def verify_zip(zip_path: Path) -> VerifyResult:
    with tempfile.TemporaryDirectory() as tmp_dir:
        extract_dir = Path(tmp_dir) / "extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)

        entries = [p for p in extract_dir.iterdir()]
        if len(entries) == 1 and entries[0].is_dir():
            return verify_run_directory(entries[0])

        return verify_run_directory(extract_dir)


def verify_path(target: str | Path) -> VerifyResult:
    target = Path(target)

    if not target.exists():
        return VerifyResult(False, 0, [f"Caminho não encontrado: {target}"])

    if target.is_file() and target.suffix.lower() == ".zip":
        return verify_zip(target)

    if target.is_dir():
        return verify_run_directory(target)

    return VerifyResult(False, 0, [f"Formato não suportado: {target}"])
