select
  count(*) as current_asset_count
from {{ ref('dim_asset') }}
where is_current
having count(*) != 1000
