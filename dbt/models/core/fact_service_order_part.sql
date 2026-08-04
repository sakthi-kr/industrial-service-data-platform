
select
  {{ generate_surrogate_key([
    "parts.service_order_id", "parts.part_id", "parts.line_number"
  ]) }} as service_order_part_key,
  orders.service_order_key,
  dimensions.part_key,
  parts.service_order_id,
  parts.part_id,
  parts.line_number,
  parts.quantity,
  parts.requested_at,
  parts.required_at,
  parts.delivered_at,
  parts.unit_cost_eur,
  parts.quantity * parts.unit_cost_eur as extended_cost_eur,
  greatest(
    0,
    case when parts.delivered_at is not null
      then {{ hours_between('parts.required_at', 'parts.delivered_at') }} end
  ) as delivery_delay_hours,
  parts.delivered_at is null
    and to_timestamp_tz('{{ var("reporting_as_of") }}') > parts.required_at
    as is_open_overdue
from {{ ref('stg_erp_service_order_parts') }} as parts
join {{ ref('fact_service_order') }} as orders using (service_order_id)
join {{ ref('dim_part') }} as dimensions using (part_id)
