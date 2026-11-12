-- Run once, as ACCOUNTADMIN, in the database and schema chosen for the capstone.
-- Replace <storage-account> with the Azure storage account name.

-- 1. Point the Day 3 storage integration at the capstone container.
--    The integration and Snowflake's app in the tenant are reused. The storage account is new,
--    so it needs its own Storage Blob Data Reader role assignment (see docs/runbook_cloud.md).
--    This replaces the whole list, which also drops the old `snowflake-in` location.
ALTER STORAGE INTEGRATION azure_int SET STORAGE_ALLOWED_LOCATIONS = (
    'azure://<storage-account>.blob.core.windows.net/capstone/'
);

-- 2. The stage points at the folder the upload script writes to.
CREATE OR REPLACE STAGE capstone_stage
    URL = 'azure://<storage-account>.blob.core.windows.net/capstone/games/'
    STORAGE_INTEGRATION = azure_int;

-- 3. Comma-separated with a header row. The header names are matched to table columns,
--    so the load does not depend on the column order. Empty values stay empty text,
--    because raw keeps the file as delivered.
CREATE OR REPLACE FILE FORMAT capstone_csv
    TYPE = CSV
    FIELD_DELIMITER = ','
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    PARSE_HEADER = TRUE
    EMPTY_FIELD_AS_NULL = FALSE
    ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE;

-- The uploaded file should be listed. If it is not, or there is an access error,
-- check the upload and the role assignment from Day 3.
LIST @capstone_stage;
