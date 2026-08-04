
{% snapshot snap_asset_history %}

{{
  config(
    target_schema='CORE',
    unique_key='asset_id',
    strategy='timestamp',
    updated_at='updated_at',
    invalidate_hard_deletes=true
  )
}}

select *
from {{ ref('stg_erp_assets') }}

{% endsnapshot %}
