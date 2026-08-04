
select
  {{ generate_surrogate_key(["sites.site_id"]) }} as site_key,
  customers.customer_key,
  sites.site_id,
  sites.customer_id,
  sites.site_name,
  sites.country_code,
  sites.region,
  sites.timezone,
  sites.site_status,
  sites.created_at,
  sites.updated_at
from {{ ref('stg_erp_sites') }} as sites
join {{ ref('dim_customer') }} as customers using (customer_id)
