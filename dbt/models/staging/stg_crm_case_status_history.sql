with source_rows as (
  select * from {{ source('raw', 'crm_case_status_history') }}
),

ranked as (
  select
    source_rows.*,
    row_number() over (
      partition by case_status_event_id
      order by _ingested_at desc nulls last, _source_row_number desc
    ) as source_rank
  from source_rows
)

select
  nullif(trim(case_status_event_id), '') as case_status_event_id,
  nullif(trim(case_id), '') as case_id,
  upper(nullif(trim(previous_status), '')) as previous_status,
  upper(nullif(trim(new_status), '')) as new_status,
  try_to_timestamp_tz(changed_at) as changed_at,
  nullif(trim(change_reason), '') as change_reason,
  _load_batch_id,
  _source_system,
  _source_file_name,
  try_to_number(_source_row_number) as _source_row_number,
  _ingested_at,
  _record_hash
from ranked
where source_rank = 1
