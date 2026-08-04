with source_rows as (
  select * from {{ source('raw', 'erp_service_order_parts') }}
),

ranked as (
  select
    source_rows.*,
    row_number() over (
      partition by service_order_id, part_id, line_number
      order by _ingested_at desc nulls last, _source_row_number desc
    ) as source_rank
  from source_rows
)

select
  nullif(trim(service_order_id), '') as service_order_id,
  nullif(trim(part_id), '') as part_id,
  try_to_number(line_number, 38, 0) as line_number,
  try_to_number(quantity, 38, 0) as quantity,
  try_to_timestamp_tz(requested_at) as requested_at,
  try_to_timestamp_tz(required_at) as required_at,
  try_to_timestamp_tz(delivered_at) as delivered_at,
  try_to_decimal(unit_cost_eur, 18, 2) as unit_cost_eur,
  _load_batch_id,
  _source_system,
  _source_file_name,
  try_to_number(_source_row_number) as _source_row_number,
  _ingested_at,
  _record_hash
from ranked
where source_rank = 1
