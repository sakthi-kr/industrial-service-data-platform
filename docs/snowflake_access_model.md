# Snowflake access model

The project uses four custom account roles. They are arranged under `ISP_ADMIN`, which is granted to Snowflake's `SYSADMIN` role so that the normal system-administration hierarchy retains oversight.

## Roles

| Role | Intended use |
|---|---|
| `ISP_LOADER` | Load accepted source records into `RAW` and write ingestion audit results |
| `ISP_TRANSFORMER` | Read `RAW` and build tested models in `STAGING`, `CORE`, and `ANALYTICS` |
| `ISP_ANALYST` | Read approved tables and views in `ANALYTICS` |
| `ISP_ADMIN` | Inherit all project roles and operate or monitor the project warehouse |

## Schema access

| Schema | Loader | Transformer | Analyst |
|---|---|---|---|
| `RAW` | Create and modify load objects | Read | None |
| `STAGING` | None | Create and modify models | None |
| `CORE` | None | Create and modify models | None |
| `ANALYTICS` | None | Create and modify models | Read |
| `OPERATIONS` | Read and write ingestion results | Read and append quality results | None |

The schemas use managed access. Object grants are therefore controlled by the schema owner or a role with grant-management authority rather than by individual object creators.

Future grants are defined for tables and views so that new dbt and ingestion objects receive the intended access automatically. The role verification scripts also include expected-denial checks to confirm that the loader cannot read reporting data, the transformer cannot write to raw source tables, and the analyst cannot modify reporting data.
