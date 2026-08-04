
with current_assets as (
  select * from {{ ref('dim_asset') }} where is_current
)

select
  {{ generate_surrogate_key(["alerts.alert_id"]) }} as equipment_alert_key,
  assets.asset_key,
  cases.service_case_key,
  alerts.alert_id,
  alerts.asset_id,
  alerts.related_case_id,
  alerts.alert_type,
  alerts.severity,
  alerts.alert_status,
  alerts.raised_at,
  alerts.acknowledged_at,
  alerts.cleared_at,
  alerts.measured_value,
  alerts.threshold_value,
  alerts.measurement_unit,
  alerts.severity = 'CRITICAL' as is_critical,
  alerts.related_case_id is not null as converted_to_case,
  case when alerts.acknowledged_at is not null
    then {{ hours_between('alerts.raised_at', 'alerts.acknowledged_at') }} end
    as acknowledgement_hours,
  case when alerts.cleared_at is not null
    then {{ hours_between('alerts.raised_at', 'alerts.cleared_at') }} end
    as clearance_hours
from {{ ref('stg_monitoring_equipment_alerts') }} as alerts
join current_assets as assets using (asset_id)
left join {{ ref('fact_service_case') }} as cases
  on alerts.related_case_id = cases.case_id
