with source_rows as (
  select * from {{ source('raw', 'erp_customers') }}
),

ranked as (
  select
    source_rows.*,
    row_number() over (
      partition by customer_id
      order by try_to_timestamp_tz(updated_at) desc nulls last, _ingested_at desc, _source_row_number desc
    ) as source_rank
  from source_rows
)

select
  nullif(trim(customer_id), '') as customer_id,
  nullif(trim(customer_name), '') as customer_name,
  upper(nullif(trim(industry), '')) as industry,
  upper(nullif(trim(customer_region), '')) as customer_region,
  upper(nullif(trim(customer_status), '')) as customer_status,
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
