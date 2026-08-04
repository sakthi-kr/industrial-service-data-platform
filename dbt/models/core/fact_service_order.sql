with orders as (
  select * from {{ ref('stg_erp_service_orders') }}
),

current_assets as (
  select * from {{ ref('dim_asset') }} where is_current
)

select
  {{ generate_surrogate_key(["orders.service_order_id"]) }} as service_order_key,
  cases.service_case_key,
  assets.asset_key,
  technicians.technician_key,
  orders.service_order_id,
  orders.case_id,
  orders.asset_id,
  orders.lead_technician_id,
  orders.order_type,
  orders.order_status,
  orders.created_at,
  orders.scheduled_start_at,
  orders.actual_start_at,
  orders.completed_at,
  orders.downtime_start_at,
  orders.downtime_end_at,
  orders.resolution_code,
  orders.created_by_source,
  orders.order_status = 'COMPLETED' as is_completed,
  orders.order_type = 'EMERGENCY_REPAIR' as is_emergency_repair,
  case
    when orders.actual_start_at is not null and orders.completed_at is not null
      then {{ hours_between('orders.actual_start_at', 'orders.completed_at') }}
  end as service_order_duration_hours,
  case
    when orders.downtime_start_at is not null and orders.downtime_end_at is not null
      then {{ hours_between('orders.downtime_start_at', 'orders.downtime_end_at') }}
  end as downtime_hours
from orders
left join {{ ref('fact_service_case') }} as cases
  on orders.case_id = cases.case_id
join current_assets as assets
  on orders.asset_id = assets.asset_id
join {{ ref('dim_technician') }} as technicians
  on orders.lead_technician_id = technicians.technician_id
