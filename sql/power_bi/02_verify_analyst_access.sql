use role ISP_ANALYST;
use warehouse INDUSTRIAL_SERVICE_WH;
use database INDUSTRIAL_SERVICE_DB;
use schema ANALYTICS;

select * from MART_KPI_SUMMARY;
select * from MART_SERVICE_OPERATIONS order by reporting_month desc limit 10;
select * from MART_ASSET_RELIABILITY where is_high_risk order by downtime_hours desc limit 10;
select * from MART_CUSTOMER_PERFORMANCE order by service_cost_eur desc limit 10;
