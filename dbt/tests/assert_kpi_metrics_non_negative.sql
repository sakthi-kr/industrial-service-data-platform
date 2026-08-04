select *
from {{ ref('mart_kpi_summary') }}
where open_case_count < 0
   or critical_open_case_count < 0
   or mean_resolution_hours < 0
   or median_resolution_hours < 0
   or total_downtime_hours < 0
   or average_part_delivery_delay_hours < 0
   or total_service_cost_eur < 0
