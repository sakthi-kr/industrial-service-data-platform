with source_rows as (
  select * from {{ source('raw', 'crm_customer_cases') }}
),

ranked as (
  select
    source_rows.*,
    row_number() over (
      partition by case_id
      order by try_to_timestamp_tz(updated_at) desc nulls last, _ingested_at desc, _source_row_number desc
    ) as source_rank
  from source_rows
)

select
  nullif(trim(case_id), '') as case_id,
  nullif(trim(customer_id), '') as customer_id,
  nullif(trim(site_id), '') as site_id,
  nullif(trim(contract_id), '') as contract_id,
  nullif(trim(asset_id), '') as asset_id,
  upper(nullif(trim(case_type), '')) as case_type,
  upper(nullif(trim(priority), '')) as priority,
  upper(nullif(trim(fault_category), '')) as fault_category,
  upper(nullif(trim(case_status), '')) as case_status,
  try_to_timestamp_tz(created_at) as created_at,
  try_to_timestamp_tz(response_due_at) as response_due_at,
  try_to_timestamp_tz(resolution_due_at) as resolution_due_at,
  try_to_timestamp_tz(first_response_at) as first_response_at,
  try_to_timestamp_tz(resolved_at) as resolved_at,
  try_to_timestamp_tz(closed_at) as closed_at,
  try_to_timestamp_tz(updated_at) as updated_at,
  _load_batch_id,
  _source_system,
  _source_file_name,
  try_to_number(_source_row_number) as _source_row_number,
  _ingested_at,
  _record_hash
from ranked
where source_rank = 1
