
# dbt setup and execution

## What dbt does here

dbt runs SQL transformations inside Snowflake. It does not copy the raw data back to the laptop.
The local command reads the model files, works out their dependency order, sends SQL to Snowflake,
and records whether each model and test succeeded.

## Local profile

The tracked `dbt/profiles.example.yml` contains no real credentials. Copy it once:

    cp dbt/profiles.example.yml dbt/profiles.yml

`dbt/profiles.yml` is ignored by Git. It refers to values from the existing ignored `.env` file.
Add this line to `.env` if it is not already present:

    DBT_SNOWFLAKE_ROLE=ISP_TRANSFORMER

The wrapper script loads `.env` before it starts dbt, so passwords do not need to be exported in
Git Bash.

## Install and confirm dbt

    python -m pip install -e ".[dev]"
    dbt --version

The expected Core and Snowflake adapter versions are 1.12.0.

## Check the connection

    python scripts/run_dbt.py debug

A successful result ends with `All checks passed!`. The active role should be `ISP_TRANSFORMER`.
This role can read `RAW` and create objects in `STAGING`, `CORE`, and `ANALYTICS` but cannot write
back to `RAW`.

## Parse before building

    python scripts/run_dbt.py parse --no-partial-parse

Parsing checks project configuration, Jinja, references, sources, tests, and the dependency graph
without creating warehouse objects.

## Build everything

    python scripts/run_dbt.py build

`dbt build` executes staging models, the asset snapshot, core models, analytical marts, and their
tests in dependency order. Stop at the first failure and inspect the model or test named in the
terminal output.

## Run parts of the project

    python scripts/run_dbt.py build --select tag:staging
    python scripts/run_dbt.py build --select tag:core
    python scripts/run_dbt.py build --select tag:marts

Use these narrower commands only for diagnosis. The completion gate uses the full build.

## Generate lineage documentation

    python scripts/run_dbt.py docs generate
    python scripts/run_dbt.py docs serve

The second command starts a local website, usually at `http://localhost:8080`. Keep that terminal
open while viewing the site and press `Ctrl+C` when finished.

## Useful cleanup

    python scripts/run_dbt.py clean

This removes generated dbt targets and logs but does not delete Snowflake tables or views.
