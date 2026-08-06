# Dashboard data dictionary

## MART_SERVICE_OPERATIONS

Monthly service metrics grouped by region, priority, and fault category. Use this table for the
Service Operations page. The four SLA count columns support correct filtered rate calculations.

## MART_ASSET_RELIABILITY

One row per current asset with customer, site, service, cost, alert, downtime, and risk attributes.
Use this table for asset-level slicers, cards, charts, and the high-risk table.

## MART_CUSTOMER_PERFORMANCE

One row per customer. This is the one side of the customer-to-asset relationship and supports the
customer cost ranking.

## MART_KPI_SUMMARY

One reconciled portfolio-wide KPI row. Use it only for the three static methodology KPIs documented
in `dax_measures.dax`; it is intentionally disconnected from slicers.
