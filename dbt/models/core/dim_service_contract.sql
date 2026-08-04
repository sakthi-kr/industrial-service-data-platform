
select
  {{ generate_surrogate_key(["contracts.contract_id"]) }} as contract_key,
  customers.customer_key,
  sites.site_key,
  contracts.contract_id,
  contracts.customer_id,
  contracts.site_id,
  contracts.contract_type,
  contracts.start_date,
  contracts.end_date,
  contracts.response_sla_hours,
  contracts.resolution_sla_hours,
  contracts.contract_status,
  contracts.created_at,
  contracts.updated_at
from {{ ref('stg_crm_service_contracts') }} as contracts
join {{ ref('dim_customer') }} as customers using (customer_id)
join {{ ref('dim_site') }} as sites using (site_id)
