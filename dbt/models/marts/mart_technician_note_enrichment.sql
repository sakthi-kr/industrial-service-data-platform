with enrichment as (
  select * from {{ source('enrichment', 'note_enrichment_results') }}
),

notes as (
  select * from {{ ref('fact_technician_note') }}
),

orders as (
  select * from {{ ref('fact_service_order') }}
),

cases as (
  select * from {{ ref('fact_service_case') }}
)

select
  notes.technician_note_key,
  notes.note_id,
  notes.service_order_id,
  orders.case_id,
  orders.asset_key,
  notes.technician_key,
  notes.note_type,
  notes.note_text,
  notes.created_at as note_created_at,
  cases.fault_category as source_fault_category,
  cases.priority as source_case_priority,
  enrichment.model_version,
  enrichment.predicted_fault_category,
  enrichment.predicted_priority,
  enrichment.predicted_component,
  enrichment.recommended_team,
  enrichment.generated_summary,
  enrichment.fault_confidence,
  enrichment.priority_confidence,
  enrichment.output_valid,
  enrichment.processed_at
from enrichment
join notes
  on enrichment.note_id = notes.note_id
join orders
  on notes.service_order_id = orders.service_order_id
left join cases
  on orders.case_id = cases.case_id
