with cases as (
  select * from {{ ref('fact_service_case') }}
),

sites as (
  select * from {{ ref('dim_site') }}
),

service_summary as (
  select * from {{ ref('int_case_service_summary') }}
)

select
  date_trunc('month', cases.created_at)::date as reporting_month,
  sites.region,
  cases.priority,
  coalesce(cases.fault_category, 'NOT_APPLICABLE') as fault_category,
  count(*) as case_count,
  count_if(cases.is_open) as open_case_count,
  count_if(cases.priority = 'CRITICAL' and cases.is_open)
    as critical_open_case_count,
  count_if(
    cases.resolution_duration_hours is not null
    and cases.case_status != 'CANCELLED'
  ) as resolved_case_count,
  count(cases.response_sla_met) as response_sla_eligible_count,
  count_if(cases.response_sla_met) as response_sla_met_count,
  count(cases.resolution_sla_met) as resolution_sla_eligible_count,
  count_if(cases.resolution_sla_met) as resolution_sla_met_count,
  avg(cases.response_duration_hours) as mean_response_hours,
  avg(
    case when cases.case_status != 'CANCELLED' then cases.resolution_duration_hours end
  ) as mean_resolution_hours,
  median(
    case when cases.case_status != 'CANCELLED' then cases.resolution_duration_hours end
  ) as median_resolution_hours,
  {{ safe_divide('count_if(cases.response_sla_met)', 'count(cases.response_sla_met)') }}
    as response_sla_compliance_rate,
  {{ safe_divide(
    'count_if(cases.resolution_sla_met)',
    'count(cases.resolution_sla_met)'
  ) }}
    as resolution_sla_compliance_rate,
  sum(coalesce(service_summary.downtime_hours, 0)) as downtime_hours,
  sum(coalesce(service_summary.service_cost_eur, 0)) as service_cost_eur
from cases
join sites using (site_key)
left join service_summary using (case_id)
group by 1, 2, 3, 4
