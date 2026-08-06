# Power BI setup

## Connection mode

Use **Import** mode for this portfolio report. The dataset is small, report interactions remain
fast, and ordinary filtering does not keep the Snowflake warehouse running. DirectQuery is not
needed for this static demonstration.

## Snowflake server value

In Snowsight, run:

    select
      lower(current_organization_name())
        || '-'
        || lower(current_account_name())
        || '.snowflakecomputing.com'
        as power_bi_server;

Copy the returned server privately.

## Connect from Power BI Desktop

1. Open the 64-bit Power BI Desktop application.
2. Select **Home → Get data → More**.
3. Select **Database → Snowflake database → Connect**.
4. Enter the server value returned by Snowflake.
5. Enter `INDUSTRIAL_SERVICE_WH` as the warehouse.
6. Open **Advanced options**.
7. Set **Role name** to `ISP_ANALYST`.
8. Set **Database** to `INDUSTRIAL_SERVICE_DB`.
9. Select **Import**, then select **OK**.
10. Sign in using the Snowflake account that has `ISP_ANALYST`.
11. In Navigator, open `INDUSTRIAL_SERVICE_DB → ANALYTICS`.
12. Select the four marts listed in `dashboards/power_bi/model_relationships.md`.
13. Select **Load**.

Do not load tables from `RAW`, `STAGING`, or `CORE`.

## Apply the theme

Select **View → Themes → Browse for themes** and choose:

    dashboards/power_bi/industrial_service_theme.json

## Create the model

Open Model view and create the single relationship described in
`dashboards/power_bi/model_relationships.md`. Remove any other automatically created relationship.

## Create the measures

Use **Home → New measure** and copy the formulas one at a time from
`dashboards/power_bi/dax_measures.dax`.

## Build and save

Follow `dashboards/power_bi/report_build_spec.md`. Save the working file as:

    C:\Users\admin\Downloads\Seimens\power-bi-working\industrial-service-dashboard.pbix

Export the completed report to:

    dashboards/power_bi/exports/industrial_service_dashboard.pdf

Save sanitized page screenshots as:

    dashboards/power_bi/screenshots/service_operations_overview.png
    dashboards/power_bi/screenshots/asset_customer_analysis.png
