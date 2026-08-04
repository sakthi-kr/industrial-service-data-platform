
select *
from {{ ref('fact_service_cost') }}
where cost_amount_eur < 0
