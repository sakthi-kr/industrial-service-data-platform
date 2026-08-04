
{% test row_count_equals(model, expected_count) %}
select
  count(*) as actual_count
from {{ model }}
having count(*) != {{ expected_count }}
{% endtest %}
