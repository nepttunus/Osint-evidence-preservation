#!/usr/bin/env bash
set -euo pipefail
validation_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd -- "${1:?Uso: bash run.sh /caminho/repositorio [pasta_resultados]}" && pwd)"
result_dir="${2:-$PWD/resultados-artigo-$(date -u +%Y%m%dT%H%M%SZ)}"
python3 -m venv "$validation_dir/.venv"
evaluation_python="$validation_dir/.venv/bin/python"
"$evaluation_python" -m pip install -r "$validation_dir/requirements-frozen.txt"
"$evaluation_python" -m playwright install chromium
"$evaluation_python" "$validation_dir/check_harness.py"
"$evaluation_python" "$validation_dir/evaluate.py" --repo "$repo_dir" --output "$result_dir" --mode all --repetitions 3 --workers 3
printf 'Resultados: %s\n' "$result_dir"
