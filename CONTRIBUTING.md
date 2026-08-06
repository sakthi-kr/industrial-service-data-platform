# Contributing

This repository is primarily a portfolio and learning project, but focused improvements are welcome.

## Before opening a pull request

1. Create a branch from `main`.
2. Keep credentials, private screenshots, generated full datasets, local dbt profiles, and Power BI working files out of Git.
3. Run the complete local gate:

```bash
python -m pip check
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m pytest
pre-commit run --all-files
```

4. Run the validator relevant to the changed area.
5. Explain the business or engineering reason for the change, not only the file edits.

## Scope

Useful contributions include corrections to documentation, tests, deterministic generation logic, SQL or dbt modelling, KPI definitions, and reproducibility improvements.

Do not submit real customer data, company-confidential information, credentials, or screenshots containing account identifiers.
