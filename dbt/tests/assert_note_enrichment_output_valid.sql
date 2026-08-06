select *
from {{ ref('mart_technician_note_enrichment') }}
where not output_valid
   or generated_summary is null
   or trim(generated_summary) = ''
