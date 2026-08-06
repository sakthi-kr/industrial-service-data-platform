use role ISP_ANALYST;
use warehouse INDUSTRIAL_SERVICE_WH;
use database INDUSTRIAL_SERVICE_DB;
use schema ANALYTICS;

select count(*) as service_operation_rows from MART_SERVICE_OPERATIONS;
select count(*) as asset_rows from MART_ASSET_RELIABILITY;
select count(*) as customer_rows from MART_CUSTOMER_PERFORMANCE;
select count(*) as kpi_rows from MART_KPI_SUMMARY;

select
  sum(case_count) as cases,
  sum(open_case_count) as open_cases,
  sum(critical_open_case_count) as critical_open_cases,
  sum(downtime_hours) as downtime_hours,
  sum(service_cost_eur) as service_cost_eur
from MART_SERVICE_OPERATIONS;

select
  count(*) as assets,
  count_if(is_high_risk) as high_risk_assets,
  sum(downtime_hours) as asset_downtime_hours,
  sum(service_cost_eur) as asset_service_cost_eur,
  sum(critical_alert_count) as critical_alerts
from MART_ASSET_RELIABILITY;
