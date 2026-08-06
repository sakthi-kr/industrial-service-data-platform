use role ISP_ANALYST;
use warehouse INDUSTRIAL_SERVICE_WH;
use database INDUSTRIAL_SERVICE_DB;
use schema ANALYTICS;

select
  region,
  sum(case_count) as cases,
  sum(open_case_count) as open_cases,
  sum(response_sla_met_count)
    / nullif(sum(response_sla_eligible_count), 0) as response_sla_rate,
  sum(resolution_sla_met_count)
    / nullif(sum(resolution_sla_eligible_count), 0) as resolution_sla_rate,
  sum(downtime_hours) as downtime_hours,
  sum(service_cost_eur) as service_cost_eur
from MART_SERVICE_OPERATIONS
group by region
order by region;

select
  customer_name,
  count(*) as asset_count,
  count_if(is_high_risk) as high_risk_asset_count,
  sum(downtime_hours) as downtime_hours,
  sum(service_cost_eur) as service_cost_eur
from MART_ASSET_RELIABILITY
group by customer_name
order by service_cost_eur desc
limit 10;
