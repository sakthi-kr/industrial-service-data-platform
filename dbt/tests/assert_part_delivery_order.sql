
select *
from {{ ref('fact_service_order_part') }}
where delivered_at < requested_at
   or required_at < requested_at
   or quantity <= 0
   or unit_cost_eur < 0
