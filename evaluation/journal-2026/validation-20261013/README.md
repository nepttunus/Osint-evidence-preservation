# Additional validation on 13 October 2026

The complete regression suite collected 25 tests.
All 25 passed in 6.22 seconds, with no failures or skipped tests.

Environment: Linux, Python 3.14.4, pytest 9.1.1,
pluggy 1.6.0 and anyio 4.15.1.
The text log, JUnit XML and installed package versions are included.

## Review of retained live-site packages

Six packages from the 6 October experiment underwent AI-assisted
visual and structural inspection. This was not independent human validation.

All six Ed25519 signatures validated using the included public keys.
SHA-256 digests and byte lengths matched for all 72 inventoried files.
No private keys were present in these exports.
Screenshots and all 35 PDF pages were reviewed.

| Sample | HTTP | Main observations |
| --- | --- | --- |
| live-docs-fastapi-1 | 200 | Empty terminal panels and overlapping PDF footer on page 17 |
| live-institution-uab-3 | 200 | Empty highlight region, blank PDF page 2 and carousel differences |
| live-news-bbc-2 | 200 | Cookie overlay, image differences and final PDF page with only a cookie banner |
| live-service-openstreetmap-2 | 200 | Map retained with different layout and map extent in the PDF |
| live-institution-cncs-1 | 517 | DiamWall mitigation response rather than institutional content |
| live-news-reuters-1 | 401 | Access-restriction notice rather than news content |

This selected sample does not establish fidelity across all 44 live packages.
The evidence packages are retained separately.
Detailed findings are reported in Section 5.4 and Table 7 of the revised article.
