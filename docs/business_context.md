# Business context

## Scenario

This project represents a fictional industrial service organisation that maintains rotating equipment at customer sites across several regions.

The service organisation supports equipment such as gas turbines, compressors, steam turbines, and industrial pumps. Its work includes responding to customer cases, inspecting equipment, completing repairs, replacing spare parts, and reviewing equipment alerts.

The operational data is split across several source systems:

- an ERP-style system containing customers, sites, assets, service orders, technicians, spare parts, and costs;
- a CRM-style system containing customer cases, service contracts, priorities, and case status history;
- an equipment-monitoring source containing operational alerts;
- technician notes containing free-text observations from inspections and repairs.

The platform will bring these sources together so that service activity can be analysed consistently.

## Business problem

The source systems record different parts of the service process, but they do not provide a single view of equipment condition, customer cases, repair work, downtime, and cost.

This creates several practical problems:

- service managers cannot easily identify cases approaching or exceeding their SLA;
- repeated failures may be hidden across separate cases and work orders;
- spare-part delays are not clearly connected to equipment downtime;
- customer-level service performance is difficult to compare;
- technician notes contain useful fault information that is not available as structured data;
- reported KPIs may use inconsistent definitions across teams.

The project addresses these problems through a tested analytics data model rather than by reproducing the source applications themselves.

## Intended users

### Service operations manager

Needs an overview of open cases, SLA performance, workload, downtime, and service cost.

### Reliability engineer

Needs asset-level history, recurring fault patterns, equipment alerts, and repeated repair information.

### Service analyst

Needs documented and reproducible data models for operational reporting and investigation.

### Account or contract manager

Needs customer-level information about open critical cases, service performance, downtime, and contract coverage.

## Decisions supported

The platform should help users answer the following questions:

1. Which open cases require immediate attention?
2. Which customers and sites have the highest equipment downtime?
3. Which assets experience repeated failures or repeated service visits?
4. Which fault categories take the longest to resolve?
5. How often are service cases resolved within their agreed SLA?
6. How often is an issue fixed during the first completed service visit?
7. Which spare-part delays contribute most to repair time and downtime?
8. Which equipment types generate the highest service cost?
9. Which equipment alerts are followed by customer cases or service orders?
10. What fault categories and equipment components are described in technician notes?

## Project scope

The project includes:

- batch ingestion from generated ERP-, CRM-, monitoring-, and note-based datasets;
- source validation and rejected-record handling;
- loading into Snowflake;
- dbt-based cleaning, integration, testing, and analytical modelling;
- service, asset, customer, SLA, downtime, and cost metrics;
- a Power BI report built from the analytics layer;
- structured enrichment of technician notes;
- operational logging, access-control scripts, automated tests, and documentation.

## Out of scope

The first version will not include:

- a real ERP or CRM deployment;
- real customer or equipment data;
- live equipment telemetry;
- real-time streaming;
- automatic control of industrial equipment;
- predictive maintenance model training;
- a production service-dispatch application;
- a customer-facing portal;
- financial accounting or invoicing;
- multilingual technician-note processing.

These areas may be represented through simplified fields where required, but they are not separate system implementations.

## Data assumptions

The generated data will use the following assumptions:

- all organisations, sites, people, assets, and service events are fictional;
- timestamps are stored in UTC;
- financial values use EUR;
- each asset belongs to one customer site at a given point in time;
- a customer case may lead to one or more service orders;
- a service order may use zero or more spare parts;
- an equipment alert may exist without a customer case;
- an unresolved case has no resolution timestamp;
- a completed service order has a completion timestamp;
- planned data-quality defects are isolated and labelled for pipeline testing.

## Success criteria

The project will be considered successful when:

- the source datasets can be generated reproducibly;
- valid records can be loaded without duplication;
- invalid records are detected and quarantined;
- Snowflake and dbt models pass their documented tests;
- analytical KPIs reconcile with independently calculated reference values;
- Power BI measures agree with the documented KPI definitions;
- technician-note enrichment is evaluated against labelled examples;
- a new user can understand and reproduce the workflow from the repository documentation.
