# Journal evaluation: October 2026

This directory provides the evaluation harness and recorded results used in the revised OSINT evidence-preservation article. The experiment distinguishes package integrity from acquisition completeness.

## Evaluated source and environment

- Original source commit: `abe721dfb95ce812b35d10eeaed286f2079e10e9`.
- Signature-required verifier correction: `a998681ab00290b9619bbb33dbb26e1de76d9174`.
- Browser experiment: 6 October 2026, Ubuntu 26.04, Python 3.14.4, Playwright 1.63.0, Chromium 153.0.8010.12.
- Three workers, three repetitions per target, 30-second navigation timeout, 90-second whole-worker limit.
- Acquisition policy: original `networkidle` navigation with no additional observation delay.
- The recorded hashes of all 13 engine Python files match the corrected implementation. The fixture and corpus hashes also match the supplied sources.

The browser experiment used the original base commit with the verifier patch applied in the working tree. Its `environment.json` records that state and the source hashes. Publishing these materials does not constitute a new execution of the tests.

## Results

| Measure | Controlled fixtures | Live websites |
|---|---:|---:|
| Scheduled attempts | 27 | 60 |
| Packages produced | 27 | 44 |
| All fixture assertions met | 24/27 | Not assessed |
| Packages reporting HTTP 200 | 27 | 38 |
| Non-success HTTP responses preserved | 0 | 6 |
| Attempts without a completed package | 0 | 16 |
| Intact directory/ZIP checks accepted | 54/54 | 88/88 |
| Modified-input checks rejected | 324/324 | 528/528 |

All 852 modified-input checks were rejected, with no verifier exceptions recorded. These are 71 packages × six mutation classes × directory/ZIP forms, not 852 independent attack classes.

Eight fixture scenarios met every assertion in all three repetitions. The delayed-DOM fixture did not capture the marker inserted after three seconds, although the resulting packages passed integrity verification. The three CNCS responses (HTTP 517) and three Reuters responses (HTTP 401) are preserved access-error responses, not successful acquisition of the intended content. No independent inspection of the raw browser evidence packages is claimed, including for HTTP 200 responses.

Eight attempts returned a 30-second navigation timeout. Eight reached the 90-second worker limit; the exact stage of those worker timeouts is not identified by the submitted records. All failed targets remain in the results.

## Signature-required verification

The earlier verifier checked a signature only when `manifest.sig` existed. Removing it allowed a modified artefact and rewritten manifest hash to be accepted. The corrected default requires the signature and public key. Existing unsigned verification fixtures were updated to use signed manifests, and ten parameterised regression checks cover missing or invalid authentication material and malformed JSON.

In the browser-independent environment, 12 original tests passed and three browser tests were blocked at startup. The corrected browser-independent suite passed 22 tests. Its synthetic audit accepted all six intact inputs and rejected all 36 modified inputs, compared with 24/36 rejections before correction. The three browser-dependent unit tests were not rerun as part of that suite; the separate browser experiment consists of the 87 attempts described above.

## Reproduce the browser evaluation

From the repository root, on a machine with Python 3.12 or later and browser dependencies:

```bash
python3 -m venv evaluation/journal-2026/.venv
evaluation/journal-2026/.venv/bin/python -m pip install -r evaluation/journal-2026/requirements-frozen.txt
sudo evaluation/journal-2026/.venv/bin/python -m playwright install-deps chromium
evaluation/journal-2026/.venv/bin/python -m playwright install chromium
evaluation/journal-2026/.venv/bin/python evaluation/journal-2026/check_harness.py
evaluation/journal-2026/.venv/bin/python evaluation/journal-2026/evaluate.py \
  --repo . --output evaluation/journal-2026/resultados-nova-execucao \
  --mode all --repetitions 3 --workers 3
```

Use a new output directory for every execution. The dependency versions reproduce the recorded Ubuntu environment; other operating systems and Python versions may produce different results. A short `run.sh` wrapper is also supplied. It installs Python dependencies and the browser but assumes system libraries are available.

The driver invokes the engine, not the browser extension. It starts its own local fixture server. It requires no authenticated external sessions. The live corpus is a purposive selection of 20 URLs, not the WEFT corpus.

Run the synthetic integrity audit without a browser:

```bash
evaluation/journal-2026/.venv/bin/python evaluation/journal-2026/audit_integrity.py \
  --repo . --output evaluation/journal-2026/resultados-integridade
```

Run the repository tests with the same environment:

```bash
evaluation/journal-2026/.venv/bin/python -m pytest tests -q
```

## Records and limits

- `browser-results-20261006/`: the four raw files supplied from the Ubuntu experiment, unchanged, plus checked aggregate counts and raw-input hashes.
- `corpus.json` and `fixtures.py`: fixed target list and nine controlled scenarios.
- `evaluate.py`, `summarize.py`, `check_harness.py`, `audit_integrity.py`: capture driver, reporting and synthetic checks.
- `baseline-pytest.*`, `corrected-pytest.*`, and the two `integrity-results` directories: historical browser-independent evidence.
- `requirements-frozen.txt` / `requirements-ubuntu26.04.txt`: browser-experiment dependencies.
- `requirements-original-integrity.txt`: earlier browser-independent environment.
- `provenance.json`: historical and browser evaluation provenance. References to a separately delivered patch are historical; the correction is incorporated in this branch's source.

No private keys or raw browser-capture bundles are included here. New executions generate private keys outside their evidence ZIPs; do not commit their `_private_keys` directories. Review captured third-party content before redistribution.

Cryptographic verification uses the included public key and does not establish an external signer identity or independently certified capture time. The acquisition engine also ignores HTTPS errors. These limits remain unchanged by requiring a manifest signature.
