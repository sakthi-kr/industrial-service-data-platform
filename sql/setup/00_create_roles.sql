-- Create the project roles and place them under SYSADMIN.
USE ROLE SECURITYADMIN;

CREATE ROLE IF NOT EXISTS ISP_LOADER
  COMMENT = 'Loads validated source records into RAW and records ingestion results';

CREATE ROLE IF NOT EXISTS ISP_TRANSFORMER
  COMMENT = 'Builds tested models in STAGING, CORE, and ANALYTICS';

CREATE ROLE IF NOT EXISTS ISP_ANALYST
  COMMENT = 'Reads approved reporting tables and views in ANALYTICS';

CREATE ROLE IF NOT EXISTS ISP_ADMIN
  COMMENT = 'Project administration role that inherits all functional roles';

GRANT ROLE ISP_LOADER TO ROLE ISP_ADMIN;
GRANT ROLE ISP_TRANSFORMER TO ROLE ISP_ADMIN;
GRANT ROLE ISP_ANALYST TO ROLE ISP_ADMIN;
GRANT ROLE ISP_ADMIN TO ROLE SYSADMIN;
