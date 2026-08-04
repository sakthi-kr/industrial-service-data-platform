
select
  {{ generate_surrogate_key(["customer_id"]) }} as customer_key,
  customer_id,
  customer_name,
  industry,
  customer_region,
  customer_status,
  created_at,
  updated_at
from {{ ref('stg_erp_customers') }}
