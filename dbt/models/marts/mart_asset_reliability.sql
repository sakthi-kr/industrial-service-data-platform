with assets as (
  select * from {{ ref('dim_asset') }} where is_current
),

sites as (
  select * from {{ ref('dim_site') }}
),

customers as (
  select * from {{ ref('dim_customer') }}
),

case_metrics as (
  select
    asset_key,
    count(*) as case_count,
    count_if(is_open) as open_case_count,
    count_if(priority = 'CRITICAL' and is_open) as critical_open_case_count
  from {{ ref('fact_service_case') }}
  where asset_key is not null
  group by asset_key
),

order_metrics as (
  select
    asset_key,
    count(*) as service_order_count,
    sum(coalesce(downtime_hours, 0)) as downtime_hours
  from {{ ref('fact_service_order') }}
  group by asset_key
),

cost_metrics as (
  select
    orders.asset_key,
    sum(costs.cost_amount_eur) as service_cost_eur
  from {{ ref('fact_service_cost') }} as costs
  join {{ ref('fact_service_order') }} as orders using (service_order_key)
  group by orders.asset_key
),

alert_metrics as (
  select
    asset_key,
    count(*) as alert_count,
    count_if(is_critical) as critical_alert_count
  from {{ ref('fact_equipment_alert') }}
  group by asset_key
)

select
  assets.asset_key,
  assets.asset_id,
  assets.site_key,
  sites.site_id,
  sites.site_name,
  sites.region,
  sites.country_code,
  customers.customer_key,
  customers.customer_id,
  customers.customer_name,
  assets.asset_name,
  assets.asset_type,
  assets.criticality,
  assets.asset_status,
  coalesce(case_metrics.case_count, 0) as case_count,
  coalesce(case_metrics.open_case_count, 0) as open_case_count,
  coalesce(case_metrics.critical_open_case_count, 0) as critical_open_case_count,
  coalesce(order_metrics.service_order_count, 0) as service_order_count,
  coalesce(order_metrics.downtime_hours, 0) as downtime_hours,
  coalesce(cost_metrics.service_cost_eur, 0) as service_cost_eur,
  coalesce(alert_metrics.alert_count, 0) as alert_count,
  coalesce(alert_metrics.critical_alert_count, 0) as critical_alert_count,
  (
    coalesce(alert_metrics.critical_alert_count, 0) > 0
    and coalesce(case_metrics.critical_open_case_count, 0) > 0
  ) or coalesce(order_metrics.downtime_hours, 0) > 72 as is_high_risk
from assets
join sites using (site_key)
join customers using (customer_key)
left join case_metrics using (asset_key)
left join order_metrics using (asset_key)
left join cost_metrics using (asset_key)
left join alert_metrics using (asset_key)
