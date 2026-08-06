select *
from {{ ref('mart_technician_note_enrichment') }}
where fault_confidence < 0
   or fault_confidence > 1
   or priority_confidence < 0
   or priority_confidence > 1
