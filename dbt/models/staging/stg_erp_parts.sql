with source_rows as (
  select * from {{ source('raw', 'erp_parts') }}
),

ranked as (
  select
    source_rows.*,
    row_number() over (
      partition by part_id
      order by try_to_timestamp_tz(updated_at) desc nulls last, _ingested_at desc, _source_row_number desc
    ) as source_rank
  from source_rows
)

select
  nullif(trim(part_id), '') as part_id,
  nullif(trim(part_name), '') as part_name,
  upper(nullif(trim(part_category), '')) as part_category,
  try_to_decimal(unit_cost_eur, 18, 2) as unit_cost_eur,
  try_to_number(standard_lead_time_days, 38, 0) as standard_lead_time_days,
  upper(nullif(trim(part_status), '')) as part_status,
  try_to_timestamp_tz(created_at) as created_at,
  try_to_timestamp_tz(updated_at) as updated_at,
  _load_batch_id,
  _source_system,
  _source_file_name,
  try_to_number(_source_row_number) as _source_row_number,
  _ingested_at,
  _record_hash
from ranked
where source_rank = 1
