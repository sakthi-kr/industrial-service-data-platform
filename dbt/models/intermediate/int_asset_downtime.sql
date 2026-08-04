{{ config(materialized='view') }}

with valid_intervals as (
  select
    asset_id,
    downtime_start_at as interval_start,
    least(
      downtime_end_at,
      to_timestamp_tz('{{ var("reporting_as_of") }}')
    ) as interval_end
  from {{ ref('fact_service_order') }}
  where order_status != 'CANCELLED'
    and downtime_start_at is not null
    and downtime_end_at is not null
    and downtime_end_at > downtime_start_at
    and downtime_start_at < to_timestamp_tz('{{ var("reporting_as_of") }}')
),

with_prior_end as (
  select
    *,
    max(interval_end) over (
      partition by asset_id
      order by interval_start, interval_end
      rows between unbounded preceding and 1 preceding
    ) as prior_max_end
  from valid_intervals
),

with_island_start as (
  select
    *,
    case
      when prior_max_end is null or interval_start > prior_max_end then 1
      else 0
    end as starts_new_island
  from with_prior_end
),

with_island_id as (
  select
    *,
    sum(starts_new_island) over (
      partition by asset_id
      order by interval_start, interval_end
      rows between unbounded preceding and current row
    ) as island_id
  from with_island_start
),

merged_intervals as (
  select
    asset_id,
    island_id,
    min(interval_start) as merged_start,
    max(interval_end) as merged_end
  from with_island_id
  group by asset_id, island_id
)

select
  asset_id,
  sum({{ hours_between('merged_start', 'merged_end') }}) as downtime_hours
from merged_intervals
group by asset_id
