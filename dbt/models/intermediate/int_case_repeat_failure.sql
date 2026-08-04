{{ config(materialized='view') }}

with cases as (
  select * from {{ ref('fact_service_case') }}
),

eligible_cases as (
  select *
  from cases
  where case_type = 'TECHNICAL_FAULT'
    and case_status != 'CANCELLED'
    and asset_id is not null
    and fault_category is not null
    and resolved_at is not null
    and resolved_at <= dateadd(
      'day',
      -30,
      to_timestamp_tz('{{ var("reporting_as_of") }}')
    )
)

select
  original.case_id,
  count(later_cases.case_id) > 0 as repeat_failure_flag
from eligible_cases as original
left join cases as later_cases
  on later_cases.case_id != original.case_id
  and later_cases.case_type = 'TECHNICAL_FAULT'
  and later_cases.case_status != 'CANCELLED'
  and later_cases.asset_id = original.asset_id
  and later_cases.fault_category = original.fault_category
  and later_cases.created_at > original.resolved_at
  and later_cases.created_at <= dateadd('day', 30, original.resolved_at)
group by original.case_id
