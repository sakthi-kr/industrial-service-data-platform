
select
  {{ generate_surrogate_key(["technician_id"]) }} as technician_key,
  technician_id,
  technician_name,
  home_region,
  specialisation,
  skill_level,
  technician_status,
  created_at,
  updated_at
from {{ ref('stg_erp_technicians') }}
