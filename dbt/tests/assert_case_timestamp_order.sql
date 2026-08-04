
select *
from {{ ref('fact_service_case') }}
where response_due_at <= created_at
   or resolution_due_at <= created_at
   or first_response_at < created_at
   or resolved_at < created_at
   or closed_at < resolved_at
