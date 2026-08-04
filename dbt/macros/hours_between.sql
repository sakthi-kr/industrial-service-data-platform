
{% macro hours_between(start_expression, end_expression) -%}
  datediff('second', {{ start_expression }}, {{ end_expression }}) / 3600.0
{%- endmacro %}
