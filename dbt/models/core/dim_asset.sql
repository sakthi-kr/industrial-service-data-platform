
select
  {{ generate_surrogate_key(["assets.asset_id", "assets.dbt_valid_from"]) }} as asset_key,
  sites.site_key,
  assets.asset_id,
  assets.site_id,
  assets.asset_name,
  assets.asset_type,
  assets.manufacturer,
  assets.model,
  assets.serial_number,
  assets.installation_date,
  assets.criticality,
  assets.asset_status,
  assets.created_at,
  assets.updated_at,
  assets.dbt_valid_from as valid_from,
  assets.dbt_valid_to as valid_to,
  assets.dbt_valid_to is null as is_current
from {{ ref('snap_asset_history') }} as assets
join {{ ref('dim_site') }} as sites using (site_id)
