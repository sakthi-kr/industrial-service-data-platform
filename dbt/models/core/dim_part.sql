
select
  {{ generate_surrogate_key(["part_id"]) }} as part_key,
  part_id,
  part_name,
  part_category,
  unit_cost_eur,
  standard_lead_time_days,
  part_status,
  created_at,
  updated_at
from {{ ref('stg_erp_parts') }}
