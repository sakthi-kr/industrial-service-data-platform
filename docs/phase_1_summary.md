# Phase 1 review

Phase 1 fixes the business meaning of the project before data generation.
The following artefacts now define the scope:

- `docs/business_context.md` — users, decisions, assumptions, and limits;
- `docs/conceptual_data_model.md` — entities and lifecycle rules;
- `docs/kpi_catalogue.md` — formulas, eligibility rules, and edge cases;
- `docs/source_to_target_mapping.md` — warehouse lineage and handling rules;
- `config/source_schema.json` — machine-readable source definitions;
- `docs/data_dictionary.md` — generated field-level reference;
- `docs/entity_relationship_diagram.md` — source-level ER diagram.

## Phase gate

- Thirteen source datasets are defined.
- Every dataset has a business key.
- Every foreign-key reference resolves to an existing field.
- KPI formulas identify their source fields and edge-case treatment.
- Source, raw, staging, core, and analytical layers are mapped.
- The asset dimension is marked for historical tracking.
- Deliberate simplifications and out-of-scope areas are documented.

Phase 2 can now generate data against a fixed contract instead of
inventing fields while the generator is being written.
