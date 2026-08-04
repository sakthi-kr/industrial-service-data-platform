{{ config(materialized='view') }}

with cases as (
  select * from {{ ref('fact_service_case') }}
),

orders as (
  select * from {{ ref('fact_service_order') }}
  where case_id is not null
),

ranked_completed_orders as (
  select
    orders.*,
    row_number() over (
      partition by case_id
      order by actual_start_at, service_order_id
    ) as completed_order_rank
  from orders
  where is_completed
    and actual_start_at is not null
    and completed_at is not null
),

eligible_first_orders as (
  select
    cases.case_id,
    first_orders.service_order_id,
    first_orders.completed_at,
    first_orders.resolution_code
  from cases
  join ranked_completed_orders as first_orders using (case_id)
  where first_orders.completed_order_rank = 1
    and cases.case_type = 'TECHNICAL_FAULT'
    and cases.case_status != 'CANCELLED'
    and first_orders.completed_at <= dateadd(
      'day',
      -30,
      to_timestamp_tz('{{ var("reporting_as_of") }}')
    )
),

repeat_visits as (
  select
    first_orders.case_id,
    count(later_orders.service_order_id) > 0 as has_repeat_visit
  from eligible_first_orders as first_orders
  left join orders as later_orders
    on later_orders.case_id = first_orders.case_id
    and later_orders.service_order_id != first_orders.service_order_id
    and later_orders.order_type in ('CORRECTIVE_REPAIR', 'EMERGENCY_REPAIR')
    and later_orders.actual_start_at > first_orders.completed_at
    and later_orders.actual_start_at <= dateadd('day', 30, first_orders.completed_at)
  group by first_orders.case_id
)

select
  first_orders.case_id,
  first_orders.service_order_id as first_completed_service_order_id,
  first_orders.completed_at as first_completed_at,
  first_orders.resolution_code as first_resolution_code,
  first_orders.resolution_code in (
    'FIXED', 'ADJUSTED', 'REPLACED_COMPONENT', 'NO_FAULT_FOUND'
  )
  and not repeat_visits.has_repeat_visit as first_time_fix_flag
from eligible_first_orders as first_orders
join repeat_visits using (case_id)
