with source_rows as (
  select * from {{ source('raw', 'erp_sites') }}
),

ranked as (
  select
    source_rows.*,
    row_number() over (
      partition by site_id
      order by try_to_timestamp_tz(updated_at) desc nulls last, _ingested_at desc, _source_row_number desc
    ) as source_rank
  from source_rows
)

select
  nullif(trim(site_id), '') as site_id,
  nullif(trim(customer_id), '') as customer_id,
  nullif(trim(site_name), '') as site_name,
  upper(nullif(trim(country_code), '')) as country_code,
  upper(nullif(trim(region), '')) as region,
  nullif(trim(timezone), '') as timezone,
  upper(nullif(trim(site_status), '')) as site_status,
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
