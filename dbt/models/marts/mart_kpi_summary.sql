with case_metrics as (
  select
    count_if(
      is_open
      and created_at <= to_timestamp_tz('{{ var("reporting_as_of") }}')
    ) as open_case_count,
    count_if(
      is_open
      and priority = 'CRITICAL'
      and created_at <= to_timestamp_tz('{{ var("reporting_as_of") }}')
    ) as critical_open_case_count,
    {{ safe_divide('count_if(response_sla_met)', 'count(response_sla_met)') }}
      as response_sla_compliance_rate,
    {{ safe_divide('count_if(resolution_sla_met)', 'count(resolution_sla_met)') }}
      as resolution_sla_compliance_rate,
    avg(
      case when case_status != 'CANCELLED' then resolution_duration_hours end
    ) as mean_resolution_hours,
    median(
      case when case_status != 'CANCELLED' then resolution_duration_hours end
    ) as median_resolution_hours
  from {{ ref('fact_service_case') }}
),

first_time_fix_metrics as (
  select
    {{ safe_divide('count_if(first_time_fix_flag)', 'count(*)') }}
      as first_time_fix_rate
  from {{ ref('int_case_first_time_fix') }}
),

repeat_failure_metrics as (
  select
    {{ safe_divide('count_if(repeat_failure_flag)', 'count(*)') }}
      as repeat_failure_rate
  from {{ ref('int_case_repeat_failure') }}
),

downtime_metrics as (
  select coalesce(sum(downtime_hours), 0) as total_downtime_hours
  from {{ ref('int_asset_downtime') }}
),

part_metrics as (
  select
    avg(case when delivery_delay_hours > 0 then delivery_delay_hours end)
      as average_part_delivery_delay_hours
  from {{ ref('fact_service_order_part') }}
),

cost_metrics as (
  select coalesce(sum(cost_amount_eur), 0) as total_service_cost_eur
  from {{ ref('fact_service_cost') }}
),

alert_metrics as (
  select
    {{ safe_divide('count_if(converted_to_case)', 'count(*)') }}
      as alert_to_case_conversion_rate
  from {{ ref('fact_equipment_alert') }}
  where raised_at <= to_timestamp_tz('{{ var("reporting_as_of") }}')
)

select
  to_timestamp_tz('{{ var("reporting_as_of") }}') as reporting_as_of,
  case_metrics.*,
  first_time_fix_metrics.first_time_fix_rate,
  repeat_failure_metrics.repeat_failure_rate,
  downtime_metrics.total_downtime_hours,
  part_metrics.average_part_delivery_delay_hours,
  cost_metrics.total_service_cost_eur,
  alert_metrics.alert_to_case_conversion_rate
from case_metrics
cross join first_time_fix_metrics
cross join repeat_failure_metrics
cross join downtime_metrics
cross join part_metrics
cross join cost_metrics
cross join alert_metrics
