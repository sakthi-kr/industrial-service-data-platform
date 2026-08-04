
select *
from {{ ref('fact_equipment_alert') }}
where acknowledged_at < raised_at
   or cleared_at < raised_at
