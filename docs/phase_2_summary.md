# Phase 2 summary

Phase 2 adds deterministic source data for the industrial service scenario.
The full files remain local, while small samples and validation metadata are tracked.

## Generated data

| Dataset | Rows |
|---|---:|
| Assets | 1,000 |
| Case status history | 37,561 |
| Customer cases | 8,000 |
| Customers | 150 |
| Equipment alerts | 20,000 |
| Parts | 300 |
| Service contracts | 500 |
| Service costs | 16,863 |
| Service-order parts | 12,000 |
| Service orders | 6,000 |
| Sites | 250 |
| Technician notes | 5,000 |
| Technicians | 100 |
| **Total** | **107,724** |

## Validation result

- Valid datasets: True
- Validation issues: 0
- Delayed part lines: 3,957
- Alerts linked to cases: 8,139
- Controlled invalid scenarios: 7

## Reproducibility

The configuration uses a fixed seed and reporting timestamp. The generator writes
SHA-256 manifests, and the automated tests compare two independent runs byte for byte.

## Phase gate

Phase 2 is complete when generation succeeds, validation reports zero issues,
all automated tests pass, and the tracked samples match the configured schema.
