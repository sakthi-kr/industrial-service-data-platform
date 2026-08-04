
with orders as (
  select * from {{ ref('stg_erp_service_orders') }}
),

costs as (
  select * from {{ ref('int_service_order_costs') }}
)

select
  orders.case_id,
  count(*) as service_order_count,
  count_if(orders.order_status = 'COMPLETED') as completed_service_order_count,
  sum(
    case
      when orders.downtime_start_at is not null and orders.downtime_end_at is not null
        then {{ hours_between('orders.downtime_start_at', 'orders.downtime_end_at') }}
      else 0
    end
  ) as downtime_hours,
  sum(coalesce(costs.total_service_cost_eur, 0)) as service_cost_eur
from orders
left join costs using (service_order_id)
where orders.case_id is not null
group by orders.case_id
