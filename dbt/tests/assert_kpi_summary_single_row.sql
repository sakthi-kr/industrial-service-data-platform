select 1
from {{ ref('mart_kpi_summary') }}
having count(*) != 1
