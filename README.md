# Modular Platform for OSINT Digital Evidence Capture and Preservation

Modular platform for capturing and preserving web-based digital evidence in OSINT contexts. The solution combines a **browser extension** for user interaction with a **local capture and preservation engine** responsible for collecting artefacts, generating metadata, hashing, creating and signing the manifest, recording chain of custody, and producing the final package.

## Overview

The project supports structured collection of digital evidence from a browser while preserving technical context and basic mechanisms for subsequent integrity verification.

### Architecture

    [Browser] -> [Browser Extension] -> [Local API / Bridge]
                                      -> [Local Capture and Preservation Engine]
                                         +-- screenshot, HTML, PDF
                                         +-- metadata, manifest, signature
                                         +-- chain of custody
                                      -> [ZIP package / output]

## Main features

- Capture initiated directly from the browser
- Retrieval of the active tab URL
- Generation of screenshot, HTML, PDF, HAR and trace artefacts
- Collection of technical execution metadata
- Hash calculation and manifest creation
- Manifest signing
- Chain-of-custody recording
- Generation of auxiliary reports
- Final ZIP packaging
- Subsequent integrity verification of a directory or ZIP package

## Requirements

- Python 3.9 or later
- Python virtual environment
- Dependencies in `requirements.txt`
- Playwright with Chromium installed
- Google Chrome or Microsoft Edge for the extension

## Installation

Create and activate a virtual environment:

    python -m venv .venv
    source .venv/bin/activate

Install dependencies:

    pip install -r requirements.txt
    python -m playwright install chromium

## Starting the local engine

Start the local API:

    uvicorn engine.api.app:app --host 127.0.0.1 --port 8000 --reload

Quick service check:

    curl http://127.0.0.1:8000/health

## Loading the browser extension

1. Open `chrome://extensions/` or `edge://extensions/`
2. Enable **Developer mode**
3. Select **Load unpacked**
4. Choose the `extension/` directory

## Usage flow

1. Open a web page in the browser
2. Open the browser extension
3. Confirm the active URL shown in the popup
4. Click **Capture evidence**
5. The extension sends the request to the local engine
6. The local engine captures the page and generates the artefacts
7. The popup displays the execution directory and final ZIP path

## Direct CLI execution

Simple capture:

    python -m engine.src.main capture https://example.com

Capture with additional options:

    python -m engine.src.main capture https://example.com --output-dir output --timeout-ms 30000 --actor cli_user

## Integrity verification

Verify an execution directory:

    python -m engine.src.main verify output/<execution_name>

Verify the final ZIP package:

    python -m engine.src.main verify output/<execution_name>/evidence_bundle.zip

## Tests

Run the test suite:

    python -m pytest -q

## Project structure

    .
    ├── engine/ (API and capture, packaging, signing and verification code)
    ├── extension/ (browser extension)
    ├── docs/
    ├── evaluation/journal-2026/ (reproducible journal evaluation)
    ├── tests/
    └── output/

## Example output

Each execution produces a structured directory containing capture artefacts, chain-of-custody data, a signed manifest, the public key, reports and an evidence ZIP package.

## Current status

The project is a **functional MVP** with a browser extension, local API, local capture and preservation engine, actual artefact generation, and integrity verification.

## Current limitations

- no multi-user support
- no remote backend
- no external qualified timestamping
- no distributed case management
- simplified chain of custody compared with formal forensic scenarios

## Final validation update

Following supervisor feedback, the project was updated to improve private-key handling.

The private key is kept outside the evidence package and is no longer included in the generated ZIP file. The ZIP package contains only the public key required for subsequent verification.

The automated test suite was also extended with a packaging test confirming that `private_key.pem` is excluded from the evidence ZIP while `public_key.pem` remains available for verification.

Final result of the original validation: **15 passed**.

## Extended journal evaluation (October 2026)

The journal revision adds a correction that makes manifest signatures mandatory and an automated evaluation with controlled pages and live public websites.

- The corrected no-browser suite passed 22 tests, including ten new regression cases.
- 87 capture attempts were executed: nine controlled scenarios and 20 public URLs, with three repetitions per target.
- 27 controlled packages and 44 live-site packages were produced. Controlled assertions passed in 24/27 executions.
- All 142 intact directory/ZIP verification checks passed. All 852 modified-input checks were rejected.
- Content inserted after three seconds was missed in all three repetitions. Six live-site packages preserved access-denied or error responses. Package integrity does not establish acquisition completeness.

Complete results, environments, limitations and reproduction commands are available in [evaluation/journal-2026](evaluation/journal-2026/README.md). The browser evaluation uses Playwright 1.63.0 on Ubuntu 26.04. No claim is made that the complete 25-test suite was rerun in the same environment.
