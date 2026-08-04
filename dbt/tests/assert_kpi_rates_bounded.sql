select *
from {{ ref('mart_kpi_summary') }}
where response_sla_compliance_rate not between 0 and 1
   or resolution_sla_compliance_rate not between 0 and 1
   or first_time_fix_rate not between 0 and 1
   or repeat_failure_rate not between 0 and 1
   or alert_to_case_conversion_rate not between 0 and 1
