
select *
from {{ ref('mart_asset_reliability') }}
where case_count < 0
   or service_order_count < 0
   or downtime_hours < 0
   or service_cost_eur < 0
   or alert_count < 0
