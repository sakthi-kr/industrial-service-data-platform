# Technician-note enrichment design

## Purpose

Technician notes contain useful fault and component information but arrive as free text. This
implementation converts each generated note into a validated record containing a fault category,
triage priority, component, recommended service team, summary, confidence values, and model version.

The implementation is intentionally small and reproducible. It does not call an external language
model and does not present generated labels as expert engineering diagnoses.

## Label construction

The labelled dataset is produced by joining generated technician notes to service orders, customer
cases, and assets. Fault category comes from the linked customer case; planned maintenance notes use
`INSPECTION`. Component and recommended-team labels use documented mappings. Triage priority is a
transparent synthetic rule based on asset criticality, service-order type, note type, and fault.

These are synthetic operational labels, not human annotations. That limitation is retained in the
evaluation report and README.

## Features and models

The model input combines note text with four operational fields that would be available at inference
time: note type, asset type, asset criticality, and service-order type. Two independent pipelines use
TF-IDF word unigrams and bigrams followed by class-weighted logistic regression:

- fault-category classifier;
- triage-priority classifier.

Scikit-learn 1.7.2 is pinned because it supports the project's Python 3.10 to 3.12 CI matrix.

## Leakage control

Multiple notes may belong to one service order. Random row splitting could put related notes in both
training and test data. The evaluation therefore uses `GroupShuffleSplit` with service-order ID as
the group, and it rejects any split with group overlap or missing target classes.

Generated notes often state the fault or component directly. The primary holdout score is therefore
reported alongside a masked-label challenge that removes exact fault and component phrases. The
challenge result is diagnostic and is not hidden when it is lower.

## Structured output

Fault and priority are model predictions. Component and recommended team are deterministic mappings
from the predicted fault. The summary is a fixed template grounded only in the note type and
predicted labels. Every record is validated against allowed labels, mappings, confidence bounds, and
required text fields before publication.

## Snowflake integration

Python publishes predictions idempotently to
`INDUSTRIAL_SERVICE_DB.STAGING.NOTE_ENRICHMENT_RESULTS` using `ISP_TRANSFORMER`. A dbt mart joins the
results to warehouse note, order, case, asset, and technician keys. `ISP_ANALYST` reads only the
resulting `ANALYTICS.MART_TECHNICIAN_NOTE_ENRICHMENT` table.

## Reported metrics

- fault-category macro F1 and accuracy;
- priority macro F1 and accuracy;
- component exact-match accuracy;
- recommended-team accuracy;
- structured-output validity rate;
- failure rate;
- mean per-note latency;
- the same metrics after direct fault and component phrases are masked.

## Limitations

The dataset is synthetic and template-driven. High standard-holdout scores do not demonstrate
performance on real field notes, spelling variation, multilingual notes, or unseen engineering
conditions. The masked-label score is included to make lexical dependence visible. The system should
be treated as a portfolio prototype requiring human review before any operational use.
