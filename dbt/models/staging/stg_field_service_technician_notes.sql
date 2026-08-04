with source_rows as (
  select * from {{ source('raw', 'field_service_technician_notes') }}
),

ranked as (
  select
    source_rows.*,
    row_number() over (
      partition by note_id
      order by _ingested_at desc nulls last, _source_row_number desc
    ) as source_rank
  from source_rows
)

select
  nullif(trim(note_id), '') as note_id,
  nullif(trim(service_order_id), '') as service_order_id,
  nullif(trim(technician_id), '') as technician_id,
  upper(nullif(trim(note_type), '')) as note_type,
  nullif(trim(note_text), '') as note_text,
  try_to_timestamp_tz(created_at) as created_at,
  _load_batch_id,
  _source_system,
  _source_file_name,
  try_to_number(_source_row_number) as _source_row_number,
  _ingested_at,
  _record_hash
from ranked
where source_rank = 1
