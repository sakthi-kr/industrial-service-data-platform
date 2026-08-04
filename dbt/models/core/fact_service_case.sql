
with cases as (
  select * from {{ ref('stg_crm_customer_cases') }}
),

current_assets as (
  select * from {{ ref('dim_asset') }} where is_current
)

select
  {{ generate_surrogate_key(["cases.case_id"]) }} as service_case_key,
  customers.customer_key,
  sites.site_key,
  contracts.contract_key,
  assets.asset_key,
  cases.case_id,
  cases.customer_id,
  cases.site_id,
  cases.contract_id,
  cases.asset_id,
  cases.case_type,
  cases.priority,
  cases.fault_category,
  cases.case_status,
  cases.created_at,
  cases.response_due_at,
  cases.resolution_due_at,
  cases.first_response_at,
  cases.resolved_at,
  cases.closed_at,
  cases.updated_at,
  case when cases.first_response_at is not null
    then {{ hours_between('cases.created_at', 'cases.first_response_at') }} end
    as response_duration_hours,
  case when cases.resolved_at is not null
    then {{ hours_between('cases.created_at', 'cases.resolved_at') }} end
    as resolution_duration_hours,
  cases.case_status in ('OPEN', 'ASSIGNED', 'IN_PROGRESS', 'WAITING_PARTS') as is_open,
  case
    when cases.case_status = 'CANCELLED' then null
    when cases.first_response_at is not null
      then cases.first_response_at <= cases.response_due_at
    when to_timestamp_tz('{{ var("reporting_as_of") }}') > cases.response_due_at then false
    else null
  end as response_sla_met,
  case
    when cases.case_status = 'CANCELLED' then null
    when cases.resolved_at is not null then cases.resolved_at <= cases.resolution_due_at
    when to_timestamp_tz('{{ var("reporting_as_of") }}') > cases.resolution_due_at then false
    else null
  end as resolution_sla_met
from cases
join {{ ref('dim_customer') }} as customers using (customer_id)
join {{ ref('dim_site') }} as sites using (site_id)
left join {{ ref('dim_service_contract') }} as contracts using (contract_id)
left join current_assets as assets using (asset_id)
