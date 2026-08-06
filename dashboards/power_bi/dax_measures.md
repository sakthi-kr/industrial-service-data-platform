# DAX measures

The copy-ready formulas are in `dax_measures.dax`. Create each measure through **Home → New
measure**. Keep all service-operations measures in `MART_SERVICE_OPERATIONS`, asset measures in
`MART_ASSET_RELIABILITY`, and customer measures in `MART_CUSTOMER_PERFORMANCE`.

Format these measures after creating them:

| Measure | Format |
|---|---|
| Response SLA % | Percentage, 1 decimal place |
| Resolution SLA % | Percentage, 1 decimal place |
| KPI First-Time-Fix % | Percentage, 1 decimal place |
| KPI Repeat Failure % | Percentage, 1 decimal place |
| Service Cost EUR | Currency, EUR, no decimal places |
| Asset Service Cost EUR | Currency, EUR, no decimal places |
| Downtime Hours | Whole number |
| Asset Downtime Hours | Whole number |
| Mean Resolution Hours | Decimal number, 1 decimal place |
| KPI Median Resolution Hours | Decimal number, 1 decimal place |

The SLA measures use numerator and denominator columns from the warehouse rather than averaging
pre-calculated percentages. This keeps the result correct when users apply filters.
