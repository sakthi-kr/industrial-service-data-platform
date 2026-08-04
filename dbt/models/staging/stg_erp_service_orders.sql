with source_rows as (
  select * from {{ source('raw', 'erp_service_orders') }}
),

ranked as (
  select
    source_rows.*,
    row_number() over (
      partition by service_order_id
      order by _ingested_at desc nulls last, _source_row_number desc
    ) as source_rank
  from source_rows
)

select
  nullif(trim(service_order_id), '') as service_order_id,
  nullif(trim(case_id), '') as case_id,
  nullif(trim(asset_id), '') as asset_id,
  nullif(trim(lead_technician_id), '') as lead_technician_id,
  upper(nullif(trim(order_type), '')) as order_type,
  upper(nullif(trim(order_status), '')) as order_status,
  try_to_timestamp_tz(created_at) as created_at,
  try_to_timestamp_tz(scheduled_start_at) as scheduled_start_at,
  try_to_timestamp_tz(actual_start_at) as actual_start_at,
  try_to_timestamp_tz(completed_at) as completed_at,
  try_to_timestamp_tz(downtime_start_at) as downtime_start_at,
  try_to_timestamp_tz(downtime_end_at) as downtime_end_at,
  upper(nullif(trim(resolution_code), '')) as resolution_code,
  upper(nullif(trim(created_by_source), '')) as created_by_source,
  _load_batch_id,
  _source_system,
  _source_file_name,
  try_to_number(_source_row_number) as _source_row_number,
  _ingested_at,
  _record_hash
from ranked
where source_rank = 1
