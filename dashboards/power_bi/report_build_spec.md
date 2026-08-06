# Report build specification

The report has two pages. Use a 16:9 canvas and the supplied theme.

## Service Operations

### Slicers

Place four dropdown slicers across the top:

1. `REPORTING_MONTH`
2. `REGION`
3. `PRIORITY`
4. `FAULT_CATEGORY`

All fields come from `MART_SERVICE_OPERATIONS`.

### KPI cards

Add six cards:

- Open Cases
- Critical Open Cases
- Response SLA %
- Resolution SLA %
- Downtime Hours
- Service Cost EUR

### Visuals

1. **Line and clustered column chart**
   - X-axis: `REPORTING_MONTH`
   - Column Y-axis: Cases
   - Line Y-axis: Open Cases
2. **Clustered bar chart**
   - Y-axis: `REGION`
   - X-axis: Cases
3. **Stacked column chart**
   - X-axis: `FAULT_CATEGORY`
   - Y-axis: Cases
   - Legend: `PRIORITY`
   - Visual filter: Top 10 by Cases
4. **Matrix**
   - Rows: `REGION`
   - Columns: `PRIORITY`
   - Values: Open Cases, Response SLA %, Resolution SLA %

Use consistent titles and sort the monthly chart in ascending date order.

## Asset and Customer Analysis

### Slicers

Use fields from `MART_ASSET_RELIABILITY`:

1. `CUSTOMER_NAME`
2. `REGION`
3. `ASSET_TYPE`
4. `CRITICALITY`
5. `ASSET_STATUS`

### KPI cards

- Asset Count
- High-Risk Assets
- Asset Downtime Hours
- Asset Service Cost EUR
- Critical Alerts

### Visuals

1. **Scatter chart**
   - X-axis: `SERVICE_COST_EUR`
   - Y-axis: `DOWNTIME_HOURS`
   - Size: `CRITICAL_ALERT_COUNT`
   - Legend: `ASSET_TYPE`
   - Details: `ASSET_ID`
2. **Clustered bar chart**
   - Y-axis: `ASSET_NAME`
   - X-axis: `DOWNTIME_HOURS`
   - Visual filter: Top 10 by downtime
3. **Asset table**
   - `ASSET_ID`
   - `ASSET_NAME`
   - `CUSTOMER_NAME`
   - `SITE_NAME`
   - `ASSET_TYPE`
   - `CRITICALITY`
   - `OPEN_CASE_COUNT`
   - `CRITICAL_ALERT_COUNT`
   - `DOWNTIME_HOURS`
   - `SERVICE_COST_EUR`
   - `IS_HIGH_RISK`
   - Filter to `IS_HIGH_RISK = True`
4. **Customer bar chart**
   - Y-axis: `MART_CUSTOMER_PERFORMANCE[CUSTOMER_NAME]`
   - X-axis: `MART_CUSTOMER_PERFORMANCE[SERVICE_COST_EUR]`
   - Visual filter: Top 10 by service cost

The relationship from the customer table to the asset table lets a customer selection filter the
asset visuals.
