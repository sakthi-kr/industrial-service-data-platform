-- Managed-access schemas keep grants under the schema owner.
USE ROLE SYSADMIN;
USE DATABASE INDUSTRIAL_SERVICE_DB;

CREATE SCHEMA IF NOT EXISTS RAW
  WITH MANAGED ACCESS
  COMMENT = 'Source records preserved with ingestion metadata';

CREATE SCHEMA IF NOT EXISTS STAGING
  WITH MANAGED ACCESS
  COMMENT = 'Typed, cleaned, and deduplicated source models';

CREATE SCHEMA IF NOT EXISTS CORE
  WITH MANAGED ACCESS
  COMMENT = 'Integrated dimensions, facts, and reusable business logic';

CREATE SCHEMA IF NOT EXISTS ANALYTICS
  WITH MANAGED ACCESS
  COMMENT = 'Reporting marts and approved analytical views';

CREATE SCHEMA IF NOT EXISTS OPERATIONS
  WITH MANAGED ACCESS
  COMMENT = 'Pipeline runs, rejected records, and quality results';
