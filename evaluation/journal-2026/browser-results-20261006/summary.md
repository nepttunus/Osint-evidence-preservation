# Observed evaluation results

Counts refer to attempts; repetitions of one site are not independent sites. Cryptographic validity is distinct from acquisition completeness. Live content requires review.

| Corpus | Attempts | Captures completed | Original directory / ZIP accepted | Fixture runs meeting assertions |
|---|---:|---:|---:|---:|
| fixture | 27 | 27 | 54/54 | 24/27 |

fixture observed capture times: median 1.805 s; range 1.573–2.115 s. Concurrent execution; not a controlled performance benchmark.

| live | 60 | 44 | 88/88 | not assessed |

live observed capture times: median 7.578 s; range 1.815–27.684 s. Concurrent execution; not a controlled performance benchmark.


| Tamper variant | Rejected / constructed checks |
|---|---:|
| artifact_modified | 142/142 |
| artifact_removed | 142/142 |
| manifest_modified | 142/142 |
| artifact_and_digest_modified | 142/142 |
| signature_removed | 142/142 |
| artifact_digest_modified_signature_removed | 142/142 |

## Per-fixture assertions

| Fixture | Complete captures | All assertions met |
|---|---:|---:|
| console | 3/3 | 3/3 |
| delayed-dom | 3/3 | 0/3 |
| dynamic | 3/3 | 3/3 |
| failed-resource | 3/3 | 3/3 |
| fetch | 3/3 | 3/3 |
| iframe | 3/3 | 3/3 |
| redirect | 3/3 | 3/3 |
| state | 3/3 | 3/3 |
| static | 3/3 | 3/3 |

Dynamic markers: 3 unique in 3 completed, assertion-passing captures.
