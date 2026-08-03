# KPI catalogue

## Purpose

This document defines the service and reliability metrics used by the project. Each KPI has one agreed formula, grain, source-field mapping, and treatment of incomplete records.

The definitions will later be implemented in Snowflake, dbt, Python validation code, and Power BI. A metric is not considered complete until those implementations produce matching results for the same test dataset.

## General conventions

- All timestamps are interpreted as UTC.
- Durations are calculated using exact timestamp differences rather than calendar-day subtraction.
- Duration values are reported in decimal hours unless another unit is stated.
- Financial values are reported in EUR.
- Cancelled cases and cancelled service orders are excluded unless a KPI explicitly includes them.
- Open records are evaluated using a supplied reporting timestamp rather than the computer's current time.
- The reporting timestamp will be stored as `reporting_as_of`.
- Percentages are stored as decimal values in analytical tables and formatted as percentages in Power BI.
- Division by zero returns `NULL`, not zero, unless a business definition explicitly states otherwise.
- Median calculations use the continuous median of the eligible population.
- Source identifiers remain available in analytical models for traceability.

## Metric dimensions

KPIs should be available, where meaningful, by:

- reporting date;
- customer;
- site;
- region;
- asset;
- asset type;
- asset criticality;
- contract type;
- case priority;
- case type;
- fault category;
- service-order type;
- technician;
- part category.

Not every KPI will support every dimension. A dimension should only be used when it is available at the KPI's natural grain.

## Case backlog metrics

### Open case count

Business question:

How many customer cases remain unresolved at the reporting timestamp?

Formula:

`count(case_id)`

Eligibility rules:

- Include cases with status `OPEN`, `ASSIGNED`, `IN_PROGRESS`, or `WAITING_PARTS`.
- Exclude `RESOLVED`, `CLOSED`, and `CANCELLED`.
- Include only cases created on or before `reporting_as_of`.

Natural grain:

One row per customer case.

Required source fields:

- `customer_cases.case_id`
- `customer_cases.case_status`
- `customer_cases.created_at`

### Critical open case count

Business question:

How many unresolved cases have critical priority?

Formula:

`count(case_id where priority = 'CRITICAL')`

Eligibility rules:

- Apply the open case definition.
- Include only cases with priority `CRITICAL`.

Required source fields:

- `customer_cases.case_id`
- `customer_cases.case_status`
- `customer_cases.priority`
- `customer_cases.created_at`

### Backlog age hours

Business question:

How long has each currently open case been in the backlog?

Formula:

`datediff_seconds(created_at, reporting_as_of) / 3600`

Eligibility rules:

- Apply the open case definition.
- Negative durations are invalid and must fail data-quality checks.

Natural grain:

One row per open case.

Required source fields:

- `customer_cases.case_id`
- `customer_cases.created_at`
- `reporting_as_of`

### Average backlog age hours

Formula:

`average(backlog_age_hours)`

Eligibility rules:

- Include eligible open cases only.
- Return `NULL` when no open cases exist.

### Backlog over 30 days count

Formula:

`count(case_id where backlog_age_hours > 720)`

The threshold uses 30 multiplied by 24 hours rather than calendar months.

## SLA metrics

### Response SLA compliance rate

Business question:

What proportion of eligible cases received a first response by the agreed response deadline?

Case-level flag:

`response_sla_met = first_response_at <= response_due_at`

Aggregate formula:

`sum(response_sla_met) / count(eligible_case_id)`

Eligibility rules:

- Exclude cancelled cases.
- Include cases with a non-null `response_due_at`.
- Include cases with a recorded `first_response_at`.
- Cases without a first response are included only when `reporting_as_of` is later than `response_due_at`; they count as breached.
- Cases still within the response window and without a response are excluded from the final denominator because their outcome is not yet known.
- A response at the exact due timestamp counts as compliant.

Required source fields:

- `customer_cases.case_id`
- `customer_cases.case_status`
- `customer_cases.first_response_at`
- `customer_cases.response_due_at`
- `reporting_as_of`

### Response SLA breach count

Formula:

`count(eligible_case_id where response_sla_met = false)`

The eligibility rules must match the response SLA compliance rate exactly.

### Resolution SLA compliance rate

Business question:

What proportion of eligible cases were resolved by the agreed resolution deadline?

Case-level flag for resolved cases:

`resolution_sla_met = resolved_at <= resolution_due_at`

Case-level flag for overdue unresolved cases:

`resolution_sla_met = false when resolved_at is null and reporting_as_of > resolution_due_at`

Aggregate formula:

`sum(resolution_sla_met) / count(eligible_case_id)`

Eligibility rules:

- Exclude cancelled cases.
- Include cases with a non-null `resolution_due_at`.
- Include resolved cases.
- Include unresolved cases only after their resolution deadline has passed.
- Exclude unresolved cases that are still within their resolution window.
- A resolution at the exact due timestamp counts as compliant.

Required source fields:

- `customer_cases.case_id`
- `customer_cases.case_status`
- `customer_cases.resolved_at`
- `customer_cases.resolution_due_at`
- `reporting_as_of`

### Resolution SLA breach count

Formula:

`count(eligible_case_id where resolution_sla_met = false)`

### Active SLA risk count

Business question:

How many unresolved cases are approaching their resolution deadline?

Formula:

`count(case_id where hours_to_resolution_due between 0 and 24)`

Where:

`hours_to_resolution_due = datediff_seconds(reporting_as_of, resolution_due_at) / 3600`

Eligibility rules:

- Include open cases only.
- Include cases whose deadline has not passed.
- Include deadlines up to and including 24 hours away.
- Exclude cases without a resolution deadline.

## Resolution-time metrics

### Case resolution time hours

Formula:

`datediff_seconds(created_at, resolved_at) / 3600`

Eligibility rules:

- Include resolved or closed cases with a non-null `resolved_at`.
- Exclude cancelled cases.
- `resolved_at` must not precede `created_at`.
- Use the first valid resolution timestamp for the initial resolution-time KPI.
- Reopened-case analysis will be handled separately through status history.

Natural grain:

One row per resolved case.

Required source fields:

- `customer_cases.case_id`
- `customer_cases.created_at`
- `customer_cases.resolved_at`
- `customer_cases.case_status`

### Mean resolution time hours

Formula:

`average(case_resolution_time_hours)`

### Median resolution time hours

Formula:

`median(case_resolution_time_hours)`

### P90 resolution time hours

Formula:

`90th percentile of case_resolution_time_hours`

This metric is included because the mean can hide a long tail of difficult service cases.

## First-time-fix metrics

### First-time-fix flag

Business question:

Was the customer issue resolved during the first completed service order?

Case-level formula:

`true when the first completed service order has a successful resolution code and no additional corrective or emergency repair order begins within 30 days`

Successful resolution codes:

- `FIXED`
- `ADJUSTED`
- `REPLACED_COMPONENT`
- `NO_FAULT_FOUND`

Eligibility rules:

- Include technical fault cases only.
- Exclude cancelled cases.
- Require at least one completed service order.
- Sort service orders by `actual_start_at`, then by `service_order_id`.
- Planned preventive-maintenance orders do not count as repeat corrective visits.
- A second corrective or emergency repair starting exactly 30 days later counts as a repeat visit and therefore fails first-time fix.
- Cases with insufficient follow-up time are excluded when the first completed order occurred less than 30 days before `reporting_as_of`.

Required source fields:

- `customer_cases.case_id`
- `customer_cases.case_type`
- `customer_cases.case_status`
- `service_orders.service_order_id`
- `service_orders.case_id`
- `service_orders.order_type`
- `service_orders.order_status`
- `service_orders.actual_start_at`
- `service_orders.completed_at`
- `service_orders.resolution_code`
- `reporting_as_of`

### First-time-fix rate

Formula:

`sum(first_time_fix_flag) / count(eligible_case_id)`

Natural grain:

One row per eligible technical fault case.

## Repeat-failure metrics

### Repeat failure flag

Business question:

Did the same asset experience another technical fault in the same fault category shortly after resolution?

Case-level formula:

`true when a later technical fault case for the same asset and fault category is created within 30 days after resolved_at`

Eligibility rules:

- Include technical fault cases with an asset, fault category, and resolution timestamp.
- Exclude cancelled cases.
- The later case must have a different `case_id`.
- The later case creation timestamp must be greater than the original resolution timestamp.
- A new case created exactly 30 days after resolution counts as a repeat failure.
- Cases resolved less than 30 days before `reporting_as_of` are excluded because the full observation window is unavailable.

Required source fields:

- `customer_cases.case_id`
- `customer_cases.asset_id`
- `customer_cases.case_type`
- `customer_cases.fault_category`
- `customer_cases.created_at`
- `customer_cases.resolved_at`
- `customer_cases.case_status`
- `reporting_as_of`

### Repeat failure rate

Formula:

`sum(repeat_failure_flag) / count(eligible_resolved_case_id)`

### Repeat failures per asset

Formula:

`count(case_id where repeat_failure_flag = true)`

Natural grain:

One row per asset per reporting period.

## Service-order metrics

### Completed service order count

Formula:

`count(service_order_id where order_status = 'COMPLETED')`

Eligibility rules:

- Exclude cancelled orders.
- Include orders completed on or before `reporting_as_of`.

### Service order duration hours

Formula:

`datediff_seconds(actual_start_at, completed_at) / 3600`

Eligibility rules:

- Include completed orders only.
- Require non-null start and completion timestamps.
- Negative durations are invalid.

### Mean service order duration hours

Formula:

`average(service_order_duration_hours)`

### Emergency repair share

Formula:

`count(completed emergency repair orders) / count(all completed eligible orders)`

## Downtime metrics

### Service-order downtime hours

Formula:

`datediff_seconds(downtime_start_at, downtime_end_at) / 3600`

Eligibility rules:

- Include service orders with both downtime timestamps.
- Exclude cancelled orders.
- Downtime end must not precede downtime start.
- Overlapping downtime intervals for the same asset must be merged before asset-level aggregation to avoid double counting.

Required source fields:

- `service_orders.service_order_id`
- `service_orders.asset_id`
- `service_orders.order_status`
- `service_orders.downtime_start_at`
- `service_orders.downtime_end_at`

### Total downtime hours

Formula:

`sum(non_overlapping_asset_downtime_hours)`

Natural grain:

One row per asset per reporting period.

### Average downtime per affected asset

Formula:

`total downtime hours / count(distinct asset_id with downtime greater than zero)`

### Downtime by asset type

Formula:

`sum(non_overlapping_asset_downtime_hours) grouped by asset_type`

Required additional fields:

- `assets.asset_id`
- `assets.asset_type`

## Spare-parts metrics

### Part delivery delay hours

Formula:

`maximum(0, datediff_seconds(required_at, delivered_at) / 3600)`

Eligibility rules:

- Include delivered part lines with non-null `required_at` and `delivered_at`.
- Early delivery produces zero delay rather than a negative value.
- Undelivered parts are handled through the open part request metric.

Required source fields:

- `service_order_parts.service_order_id`
- `service_order_parts.part_id`
- `service_order_parts.line_number`
- `service_order_parts.required_at`
- `service_order_parts.delivered_at`

### Delayed part line count

Formula:

`count(part_line where part_delivery_delay_hours > 0)`

### Average part delivery delay hours

Formula:

`average(part_delivery_delay_hours where part_delivery_delay_hours > 0)`

This metric describes delayed lines only. A separate overall average may be calculated when needed but must be labelled clearly.

### Open overdue part request count

Formula:

`count(part_line where delivered_at is null and reporting_as_of > required_at)`

### Downtime associated with part delay

Business question:

How much downtime occurred on orders that had at least one delayed part line?

Formula:

`sum(non_overlapping downtime hours for service orders with delayed part lines)`

This is an association metric. It must not be described as downtime caused by the part delay unless a separate causal field is introduced.

## Cost metrics

### Service-order cost

Formula:

`sum(cost_amount_eur) grouped by service_order_id`

Eligibility rules:

- Exclude invalid negative costs.
- Include all allowed cost types.
- Do not add service-order part costs separately when they are already represented by `PART` cost records.

Required source fields:

- `service_costs.service_cost_id`
- `service_costs.service_order_id`
- `service_costs.cost_type`
- `service_costs.cost_amount_eur`

### Total service cost

Formula:

`sum(service_order_cost_eur)`

### Average service cost per completed order

Formula:

`total service cost for completed orders / count(distinct completed service_order_id)`

### Service cost per asset

Formula:

`sum(service_order_cost_eur) grouped by asset_id`

### Service cost per resolved case

Formula:

`sum(costs linked through service orders) / count(distinct resolved case_id)`

Eligibility rules:

- Include resolved or closed cases.
- Exclude cancelled cases.
- Include cases with zero recorded cost in the denominator when they otherwise meet the eligibility rules.

## Equipment-alert metrics

### Alert count

Formula:

`count(alert_id)`

### Critical alert count

Formula:

`count(alert_id where severity = 'CRITICAL')`

### Alert acknowledgement time hours

Formula:

`datediff_seconds(raised_at, acknowledged_at) / 3600`

Eligibility rules:

- Include alerts with a non-null acknowledgement timestamp.
- Acknowledgement must not precede alert creation.

### Alert-to-case conversion rate

Business question:

What proportion of equipment alerts are followed by a related customer case?

Alert-level flag:

`true when related_case_id is not null`

Aggregate formula:

`sum(alert_converted_to_case) / count(eligible_alert_id)`

Eligibility rules:

- Include alerts raised on or before `reporting_as_of`.
- Exclude alerts whose asset or case references fail validation.
- The first implementation uses the explicit `related_case_id` field rather than inferring a relationship by time proximity.

### Critical alert clearance time hours

Formula:

`datediff_seconds(raised_at, cleared_at) / 3600`

Eligibility rules:

- Include critical alerts with a non-null clearance timestamp.
- Clearance must not precede alert creation.

## Customer and asset metrics

### Assets under active contract

Formula:

`count(distinct asset_id at sites covered by an active contract)`

Eligibility rules:

- Contract start date must be on or before the reporting date.
- Contract end date must be on or after the reporting date.
- Exclude cancelled contracts.
- An asset is counted once even if overlapping contracts exist.

### Cases per active asset

Formula:

`count(eligible case_id) / count(distinct active asset_id)`

The reporting period must be stated whenever this metric is displayed.

### Service cost per active asset

Formula:

`total service cost / count(distinct active asset_id)`

### High-risk asset flag

An asset is marked high risk when at least two of the following are true during the selected reporting period:

- at least two repeat failures;
- at least one critical alert;
- downtime greater than 72 hours;
- service cost above the 90th percentile for its asset type;
- at least one open critical case.

This is a transparent business rule, not a predictive model.

## Technician-note enrichment metrics

These metrics will be added after the labelled evaluation dataset is created.

### Fault-category macro F1

Formula:

Unweighted mean of the F1 scores calculated separately for each fault category.

### Priority accuracy

Formula:

`correct priority predictions / total evaluated notes`

### Component extraction accuracy

Formula:

`exactly matched component labels / total evaluated notes`

### Structured output validity rate

Formula:

`valid enrichment records / total attempted enrichment records`

A valid record must contain all required fields and use allowed category values.

### Enrichment failure rate

Formula:

`failed enrichment attempts / total attempted enrichment records`

## Reporting-period rules

Metrics based on events must define which timestamp places the record into a reporting period.

| Metric area | Reporting timestamp |
|---|---|
| New cases | `customer_cases.created_at` |
| Resolved cases | `customer_cases.resolved_at` |
| Closed cases | `customer_cases.closed_at` |
| Service orders | `service_orders.completed_at` |
| Costs | `service_costs.cost_recorded_at` |
| Alerts | `equipment_alerts.raised_at` |
| Technician notes | `technician_notes.created_at` |
| Downtime | Interval overlap with the reporting period |
| Backlog | State at `reporting_as_of` |

Downtime intervals that cross reporting-period boundaries must be clipped to the selected period before aggregation.

## Required reconciliation tests

The following metrics must be calculated independently in Python and Snowflake and compared on a fixed test dataset:

- open case count;
- critical open case count;
- response SLA compliance rate;
- resolution SLA compliance rate;
- mean resolution time;
- median resolution time;
- first-time-fix rate;
- repeat failure rate;
- total downtime hours;
- average part delivery delay;
- total service cost;
- alert-to-case conversion rate.

Comparison rules:

- integer counts must match exactly;
- monetary values must match to two decimal places;
- duration values must match within one second;
- rates must match within `0.000001`;
- null results must match null results.

## Known limitations

- SLA pauses during customer waiting time are not modelled in the first version.
- Working-hour calendars and public holidays are not applied; SLA durations use elapsed hours.
- The first-time-fix definition uses a 30-day follow-up window rather than a service-contract-specific window.
- Repeat failure is based on the same fault category, not engineering root-cause analysis.
- Downtime associated with a delayed part does not prove that the delay caused the downtime.
- The high-risk asset flag is a rule-based indicator and must not be presented as a failure probability.
