# Entity relationship diagram

This diagram shows the source-level business entities and their keys.
Optional links remain nullable in the source catalogue.

```mermaid
erDiagram
    CUSTOMERS {
        string customer_id PK
        string customer_name
        string industry
        string customer_region
        string customer_status
        datetime created_at
        datetime updated_at
    }
    SITES {
        string site_id PK
        string customer_id FK
        string site_name
        string country_code
        string region
        string timezone
        string site_status
        datetime created_at
        datetime updated_at
    }
    ASSETS {
        string asset_id PK
        string site_id FK
        string asset_name
        string asset_type
        string manufacturer
        string model
        string serial_number
        date installation_date
        string criticality
        string asset_status
        datetime created_at
        datetime updated_at
    }
    SERVICE_CONTRACTS {
        string contract_id PK
        string customer_id FK
        string site_id FK
        string contract_type
        date start_date
        date end_date
        int response_sla_hours
        int resolution_sla_hours
        string contract_status
        datetime created_at
        datetime updated_at
    }
    CUSTOMER_CASES {
        string case_id PK
        string customer_id FK
        string site_id FK
        string contract_id FK
        string asset_id FK
        string case_type
        string priority
        string fault_category
        string case_status
        datetime created_at
        datetime response_due_at
        datetime resolution_due_at
        datetime first_response_at
        datetime resolved_at
        datetime closed_at
        datetime updated_at
    }
    CASE_STATUS_HISTORY {
        string case_status_event_id PK
        string case_id FK
        string previous_status
        string new_status
        datetime changed_at
        string change_reason
    }
    TECHNICIANS {
        string technician_id PK
        string technician_name
        string home_region
        string specialisation
        string skill_level
        string technician_status
        datetime created_at
        datetime updated_at
    }
    SERVICE_ORDERS {
        string service_order_id PK
        string case_id FK
        string asset_id FK
        string lead_technician_id FK
        string order_type
        string order_status
        datetime created_at
        datetime scheduled_start_at
        datetime actual_start_at
        datetime completed_at
        datetime downtime_start_at
        datetime downtime_end_at
        string resolution_code
        string created_by_source
    }
    PARTS {
        string part_id PK
        string part_name
        string part_category
        decimal unit_cost_eur
        int standard_lead_time_days
        string part_status
        datetime created_at
        datetime updated_at
    }
    SERVICE_ORDER_PARTS {
        string service_order_id PK, FK
        string part_id PK, FK
        int line_number PK
        int quantity
        datetime requested_at
        datetime required_at
        datetime delivered_at
        decimal unit_cost_eur
    }
    SERVICE_COSTS {
        string service_cost_id PK
        string service_order_id FK
        string cost_type
        decimal cost_amount_eur
        datetime cost_recorded_at
    }
    EQUIPMENT_ALERTS {
        string alert_id PK
        string asset_id FK
        string related_case_id FK
        string alert_type
        string severity
        string alert_status
        datetime raised_at
        datetime acknowledged_at
        datetime cleared_at
        decimal measured_value
        decimal threshold_value
        string measurement_unit
    }
    TECHNICIAN_NOTES {
        string note_id PK
        string service_order_id FK
        string technician_id FK
        string note_type
        string note_text
        datetime created_at
    }
    CUSTOMERS ||--o{ SITES : owns
    CUSTOMERS ||--o{ SERVICE_CONTRACTS : holds
    SITES ||--o{ SERVICE_CONTRACTS : covered by
    SITES ||--o{ ASSETS : contains
    CUSTOMERS ||--o{ CUSTOMER_CASES : raises
    SITES ||--o{ CUSTOMER_CASES : reports
    SERVICE_CONTRACTS o|--o{ CUSTOMER_CASES : governs
    ASSETS o|--o{ CUSTOMER_CASES : concerns
    CUSTOMER_CASES ||--|{ CASE_STATUS_HISTORY : has history
    CUSTOMER_CASES o|--o{ SERVICE_ORDERS : creates
    ASSETS ||--o{ SERVICE_ORDERS : receives
    TECHNICIANS ||--o{ SERVICE_ORDERS : leads
    SERVICE_ORDERS ||--o{ SERVICE_ORDER_PARTS : uses
    PARTS ||--o{ SERVICE_ORDER_PARTS : appears on
    SERVICE_ORDERS ||--o{ SERVICE_COSTS : incurs
    ASSETS ||--o{ EQUIPMENT_ALERTS : generates
    CUSTOMER_CASES o|--o{ EQUIPMENT_ALERTS : linked to
    SERVICE_ORDERS ||--o{ TECHNICIAN_NOTES : documents
    TECHNICIANS ||--o{ TECHNICIAN_NOTES : writes
```
