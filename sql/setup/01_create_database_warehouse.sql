-- Create the database and cost-conscious virtual warehouse.
USE ROLE SYSADMIN;

CREATE DATABASE IF NOT EXISTS INDUSTRIAL_SERVICE_DB
  DATA_RETENTION_TIME_IN_DAYS = 1
  COMMENT = 'Industrial service source, transformation, and reporting data';

CREATE WAREHOUSE IF NOT EXISTS INDUSTRIAL_SERVICE_WH
  WAREHOUSE_TYPE = 'STANDARD'
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE
  COMMENT = 'Small warehouse for ingestion, transformation, and portfolio analysis';
