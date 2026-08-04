with source_rows as (
  select * from {{ source('raw', 'erp_technicians') }}
),

ranked as (
  select
    source_rows.*,
    row_number() over (
      partition by technician_id
      order by try_to_timestamp_tz(updated_at) desc nulls last, _ingested_at desc, _source_row_number desc
    ) as source_rank
  from source_rows
)

select
  nullif(trim(technician_id), '') as technician_id,
  nullif(trim(technician_name), '') as technician_name,
  upper(nullif(trim(home_region), '')) as home_region,
  upper(nullif(trim(specialisation), '')) as specialisation,
  upper(nullif(trim(skill_level), '')) as skill_level,
  upper(nullif(trim(technician_status), '')) as technician_status,
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
