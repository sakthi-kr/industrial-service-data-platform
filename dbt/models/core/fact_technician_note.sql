
select
  {{ generate_surrogate_key(["notes.note_id"]) }} as technician_note_key,
  orders.service_order_key,
  technicians.technician_key,
  notes.note_id,
  notes.service_order_id,
  notes.technician_id,
  notes.note_type,
  notes.note_text,
  notes.created_at
from {{ ref('stg_field_service_technician_notes') }} as notes
join {{ ref('fact_service_order') }} as orders using (service_order_id)
join {{ ref('dim_technician') }} as technicians using (technician_id)
