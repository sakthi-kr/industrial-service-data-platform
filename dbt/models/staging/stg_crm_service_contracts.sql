with source_rows as (
  select * from {{ source('raw', 'crm_service_contracts') }}
),

ranked as (
  select
    source_rows.*,
    row_number() over (
      partition by contract_id
      order by try_to_timestamp_tz(updated_at) desc nulls last, _ingested_at desc, _source_row_number desc
    ) as source_rank
  from source_rows
)

select
  nullif(trim(contract_id), '') as contract_id,
  nullif(trim(customer_id), '') as customer_id,
  nullif(trim(site_id), '') as site_id,
  upper(nullif(trim(contract_type), '')) as contract_type,
  try_to_date(start_date) as start_date,
  try_to_date(end_date) as end_date,
  try_to_number(response_sla_hours, 38, 0) as response_sla_hours,
  try_to_number(resolution_sla_hours, 38, 0) as resolution_sla_hours,
  upper(nullif(trim(contract_status), '')) as contract_status,
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
