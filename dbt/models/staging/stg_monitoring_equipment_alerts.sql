with source_rows as (
  select * from {{ source('raw', 'monitoring_equipment_alerts') }}
),

ranked as (
  select
    source_rows.*,
    row_number() over (
      partition by alert_id
      order by _ingested_at desc nulls last, _source_row_number desc
    ) as source_rank
  from source_rows
)

select
  nullif(trim(alert_id), '') as alert_id,
  nullif(trim(asset_id), '') as asset_id,
  nullif(trim(related_case_id), '') as related_case_id,
  upper(nullif(trim(alert_type), '')) as alert_type,
  upper(nullif(trim(severity), '')) as severity,
  upper(nullif(trim(alert_status), '')) as alert_status,
  try_to_timestamp_tz(raised_at) as raised_at,
  try_to_timestamp_tz(acknowledged_at) as acknowledged_at,
  try_to_timestamp_tz(cleared_at) as cleared_at,
  try_to_decimal(measured_value, 18, 6) as measured_value,
  try_to_decimal(threshold_value, 18, 6) as threshold_value,
  nullif(trim(measurement_unit), '') as measurement_unit,
  _load_batch_id,
  _source_system,
  _source_file_name,
  try_to_number(_source_row_number) as _source_row_number,
  _ingested_at,
  _record_hash
from ranked
where source_rank = 1
