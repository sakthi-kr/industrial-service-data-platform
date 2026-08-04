with source_rows as (
  select * from {{ source('raw', 'erp_service_costs') }}
),

ranked as (
  select
    source_rows.*,
    row_number() over (
      partition by service_cost_id
      order by _ingested_at desc nulls last, _source_row_number desc
    ) as source_rank
  from source_rows
)

select
  nullif(trim(service_cost_id), '') as service_cost_id,
  nullif(trim(service_order_id), '') as service_order_id,
  upper(nullif(trim(cost_type), '')) as cost_type,
  try_to_decimal(cost_amount_eur, 18, 2) as cost_amount_eur,
  try_to_timestamp_tz(cost_recorded_at) as cost_recorded_at,
  _load_batch_id,
  _source_system,
  _source_file_name,
  try_to_number(_source_row_number) as _source_row_number,
  _ingested_at,
  _record_hash
from ranked
where source_rank = 1
