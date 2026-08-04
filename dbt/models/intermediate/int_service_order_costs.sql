
select
  service_order_id,
  sum(cost_amount_eur) as total_service_cost_eur,
  sum(case when cost_type = 'LABOUR' then cost_amount_eur else 0 end) as labour_cost_eur,
  sum(case when cost_type = 'TRAVEL' then cost_amount_eur else 0 end) as travel_cost_eur,
  sum(case when cost_type = 'PART' then cost_amount_eur else 0 end) as part_cost_eur,
  sum(case when cost_type = 'EXTERNAL_SERVICE' then cost_amount_eur else 0 end)
    as external_service_cost_eur
from {{ ref('stg_erp_service_costs') }}
group by service_order_id
