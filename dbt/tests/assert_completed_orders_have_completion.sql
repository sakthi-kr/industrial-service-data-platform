
select *
from {{ ref('fact_service_order') }}
where order_status = 'COMPLETED'
  and (actual_start_at is null or completed_at is null or completed_at < actual_start_at)
