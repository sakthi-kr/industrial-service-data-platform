
select
  service_order_id,
  part_id,
  line_number,
  count(*) as row_count
from {{ ref('stg_erp_service_order_parts') }}
group by 1, 2, 3
having count(*) > 1
