
select
  {{ generate_surrogate_key(["costs.service_cost_id"]) }} as service_cost_key,
  orders.service_order_key,
  costs.service_cost_id,
  costs.service_order_id,
  costs.cost_type,
  costs.cost_amount_eur,
  costs.cost_recorded_at
from {{ ref('stg_erp_service_costs') }} as costs
join {{ ref('fact_service_order') }} as orders using (service_order_id)
