# Synthetic data design

## Why the project uses generated data

The source systems represented in this project would normally contain customer, equipment,
contract, service, and technician information that cannot be published. The repository therefore
uses generated records with the same relationships and operational constraints needed by the later
Snowflake, dbt, and Power BI work.

The generator is intended to produce useful test data, not random columns that happen to share an
identifier. Asset age, equipment criticality, case priority, repair work, part delivery, downtime,
cost, and equipment alerts are linked so that the analytical results have plausible patterns.

## Generation controls

The generation settings are stored in `config/data_generation.json`.

The main controls are:

- a fixed random seed;
- the beginning of the reporting history;
- a fixed reporting timestamp;
- the requested number of rows for the main datasets;
- separate locations for full generated data and small tracked samples;
- the number of sample rows retained for each dataset.

The full files are written to `data/generated/`, which is excluded from Git. Small examples are
written to `data/samples/phase2/` so that the source shapes can be inspected directly on GitHub.

## Dataset scale

The default configuration produces:

| Dataset | Configured rows |
|---|---:|
| Customers | 150 |
| Sites | 250 |
| Assets | 1,000 |
| Service contracts | 500 |
| Customer cases | 8,000 |
| Technicians | 100 |
| Service orders | 6,000 |
| Parts | 300 |
| Service-order part lines | 12,000 |
| Equipment alerts | 20,000 |
| Technician notes | 5,000 |

Case-status events and service-cost transactions are derived from the generated cases and orders,
so their final counts are reported after each run rather than fixed in advance.

## Patterns built into the data

### Asset usage and failures

Older and more critical assets receive a higher probability of customer cases and monitoring
alerts. Retired assets remain available for historical records but receive much less new activity.

Fault categories are related to equipment type. For example, compressors are more likely to have
vibration, bearing, pressure, seal, or lubrication issues, while industrial pumps are more likely
to have flow, pressure, seal, bearing, or electrical issues.

### Cases and contracts

Cases inherit their customer and site from the selected asset. Where an applicable contract exists,
the response and resolution deadlines use its SLA settings. Case priority is influenced by asset
criticality, and older cases are more likely to be resolved or closed than recently created cases.

Each case receives a status history beginning with `OPEN`. Later events follow the case lifecycle
defined in the conceptual data model.

### Service work and part delays

Most corrective and emergency orders are linked to customer cases. Planned maintenance orders can
exist without a case. Technician selection favours the required specialisation and the asset's
service region.

Each order receives an internal part-delay propensity. The same value influences both repair
duration and the probability that a required part arrives late. This creates a measurable
relationship between part availability and longer service work without claiming that every delay
causes downtime.

### Costs

Service costs are generated as separate transactions. Non-cancelled orders normally receive labour
and travel costs. Orders using parts receive a part-cost transaction, and a smaller share receive an
external-service cost.

Part costs are not added twice. The source part lines describe quantity and unit cost, while the
service-cost table contains the accounting-style transaction used in later cost aggregation.

### Equipment alerts

Alert types are related to asset type and, where an alert is linked to a case, to the case fault
category. Severity is influenced by asset criticality and case priority. Alert timestamps follow the
`OPEN`, `ACKNOWLEDGED`, and `CLEARED` lifecycle.

### Technician notes

Technician notes are assembled from controlled templates using the service order, equipment type,
fault category, and resolution context. The notes are varied enough for the later classification
and summarisation task while retaining known labels for evaluation.

## Controlled invalid examples

Valid source files and deliberately invalid examples are kept separate. The invalid examples cover:

- a missing asset identifier;
- an unsupported case status;
- an unknown customer reference;
- a case resolved before it was created;
- a duplicate service-order identifier;
- a negative service cost;
- an empty technician note.

The expected validation code for each example is stored in `invalid/invalid_manifest.json`. These
records will later be used to test rejected-record handling in the ingestion pipeline.

## Reproducibility

The generator uses only the Python standard library. Given the same schema, configuration, and code,
it writes the same CSV and JSON content on every run.

Each output directory contains a manifest with SHA-256 hashes. The tests also generate the same
small dataset twice in different directories and compare the resulting file hashes.

## Validation

Generation does not finish successfully unless the valid datasets pass:

- required-field checks;
- data-type checks;
- allowed-value checks;
- business-key uniqueness checks;
- foreign-key checks;
- timestamp-order checks;
- customer, site, contract, asset, case, and order consistency checks;
- non-negative monetary-value checks;
- positive quantity and line-number checks;
- non-empty technician-note checks.

A JSON validation report is written beside the generated files and copied into the tracked sample
directory.

## Commands

Generate the full datasets and tracked samples:

    python -m industrial_service_platform generate-data

Validate an existing generated dataset:

    python -m industrial_service_platform validate-data

The wrapper scripts provide the same commands:

    python scripts/generate_synthetic_data.py
    python scripts/validate_synthetic_data.py

## Limits of the generated data

The data is designed for an analytics portfolio project. It does not reproduce every rule found in
a real ERP, CRM, field-service, or equipment-monitoring system.

The generator does not model inventory balances, purchase orders, technician shifts, contract
billing, public-holiday SLA calendars, or continuous sensor telemetry. Those omissions are
deliberate so the project remains focused on ingestion, data modelling, quality checks, and service
analytics.
