
with customers as (
  select * from {{ ref('dim_customer') }}
),

sites as (
  select * from {{ ref('dim_site') }}
),

assets as (
  select * from {{ ref('dim_asset') }} where is_current
),

case_metrics as (
  select
    customer_key,
    count(*) as case_count,
    count_if(is_open) as open_case_count,
    count_if(priority = 'CRITICAL' and is_open) as critical_open_case_count,
    {{ safe_divide('count_if(resolution_sla_met)', 'count(resolution_sla_met)') }}
      as resolution_sla_compliance_rate
  from {{ ref('fact_service_case') }}
  group by customer_key
),

asset_metrics as (
  select
    sites.customer_key,
    count(*) as active_asset_count
  from assets
  join sites using (site_key)
  where assets.asset_status = 'ACTIVE'
  group by sites.customer_key
),

service_metrics as (
  select
    sites.customer_key,
    sum(asset_mart.downtime_hours) as downtime_hours,
    sum(asset_mart.service_cost_eur) as service_cost_eur
  from {{ ref('mart_asset_reliability') }} as asset_mart
  join sites using (site_key)
  group by sites.customer_key
)

select
  customers.customer_key,
  customers.customer_id,
  customers.customer_name,
  customers.industry,
  customers.customer_region,
  coalesce(asset_metrics.active_asset_count, 0) as active_asset_count,
  coalesce(case_metrics.case_count, 0) as case_count,
  coalesce(case_metrics.open_case_count, 0) as open_case_count,
  coalesce(case_metrics.critical_open_case_count, 0) as critical_open_case_count,
  case_metrics.resolution_sla_compliance_rate,
  coalesce(service_metrics.downtime_hours, 0) as downtime_hours,
  coalesce(service_metrics.service_cost_eur, 0) as service_cost_eur
from customers
left join case_metrics using (customer_key)
left join asset_metrics using (customer_key)
left join service_metrics using (customer_key)
