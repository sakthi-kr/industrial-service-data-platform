# Power BI model

Load these four Snowflake tables from `INDUSTRIAL_SERVICE_DB.ANALYTICS`:

- `MART_SERVICE_OPERATIONS`
- `MART_ASSET_RELIABILITY`
- `MART_CUSTOMER_PERFORMANCE`
- `MART_KPI_SUMMARY`

Create one active relationship:

| From | Cardinality | To | Filter direction |
|---|---|---|---|
| `MART_CUSTOMER_PERFORMANCE[CUSTOMER_ID]` | One | `MART_ASSET_RELIABILITY[CUSTOMER_ID]` | Single |

Leave `MART_SERVICE_OPERATIONS` disconnected because its natural grain is a monthly operational
summary. Leave `MART_KPI_SUMMARY` disconnected because it contains one reconciled portfolio-wide
KPI row.

Power BI may try to create additional relationships automatically. Delete any relationship other
than the customer-to-asset relationship above.
