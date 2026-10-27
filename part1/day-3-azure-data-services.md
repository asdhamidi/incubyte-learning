# Part 1 · Day 3 — Azure Data Services

**Date completed:** 2026-10-26 · **Time spent:** ~10 hours
## Success criteria
| Criterion (copied from the planner)                                                                                                                           | Done? | Evidence (link or section below)                                                          |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- | ----------------------------------------------------------------------------------------- |
| Study: the Azure services in the data path - Data Factory for orchestration and copy and Blob Storage for files and Azure SQL Database for relational sources | Yes   | [Azure services in the data path](#azure-services-in-the-data-path)                       |
| Learn: mapping what you know from AWS to Azure - S3 to Blob Storage and Glue and Step Functions to Data Factory and RDS to Azure SQL                          | Yes   | [Mapping from AWS to Azure](#mapping-from-aws-to-azure)                                   |
| Learn: Data Factory building blocks - pipelines and activities and datasets and linked services and triggers                                                  | Yes   | [Data Factory building blocks](#data-factory-building-blocks)                             |
| Practice: in an Azure free account deploy the Data Factory quickstart and run a copy pipeline into Blob Storage                                               | Yes   | [Quickstart copy pipeline](#quickstart-copy-pipeline)                                     |
| Practice: create a small Azure SQL Database table and use Data Factory to copy data between it and Blob Storage                                               | Yes   | [Copying between Blob Storage and Azure SQL](#copying-between-blob-storage-and-azure-sql) |
| Learn: loading from Azure Blob Storage into Snowflake through an external stage                                                                               | Yes   | [Loading from Blob Storage into Snowflake](#loading-from-blob-storage-into-snowflake)     |
| Exercise: land a CSV in Blob Storage and load it into a Snowflake table                                                                                       | Yes   | [Loading from Blob Storage into Snowflake](#loading-from-blob-storage-into-snowflake)     |
| Exercise: add a schedule trigger and explain what happens if the file arrives late                                                                            | Yes   | [Scheduling and late-arriving files](#scheduling-and-late-arriving-files)                 |
| Reflection: which parts of your AWS experience carried over and which did not                                                                                 | Yes   | [Reflection](#azure-reflection)                                                           |
## Key learnings
- Learnt about Azure architecture and how tenants, resource groups, and services are structured.
- Got hands-on about the different services and how to integrate them and use them.
- Made a mental map from AWS to Azure for each service and I can swap them out.
- Built small ADF pipelines to move data.
- Got familiar with Azure UI and how to navigate through it.
## Exercises
- Built a pipeline to move file across containers using ADF
- Built on previous pipeline to move data from a container to a SQL database
- Built an integration between Azure and Snowflake using external stage to move data from Azure into Snowflake.
## Reflection
- Getting onto Azure has been a bit of mental adjustment. I have worked with AWS for so long that certain names have become synonymous with certain tasks. Making a direct 1:1 mapping with Azure has been a bit difficult. There is still scope for me to explore more and learn how can I do certain things in Azure that I have done in AWS.
- The ideas and concepts do carry over, but the semantics and jargon does change quite a bit. I know how to get something done in Azure now, but it would take more time and practice to do it with complete ease.
## AI use
- I used Claude to guide me through the concepts, UI, and exercises and help understand various concepts with counter-questioning and doubt clearing. 
- I also used it to format and organize the rough notes into proper steps. The language might sound too LLM-ish, but it is just formatted version of my rough notes.
## Open questions
NA
## Changes after review
NA

---
## Notes

### Azure architecture
Azure is a hierarchy. Each level decides something different: who is billed, who has access, and what the resources are.
- **Tenant:** the directory for an organization, managed by Microsoft Entra ID (users, groups, applications). Every subscription belongs to one tenant. Snowflake's integration trusts the tenant, not the subscription.
- **Management groups:** optional containers above subscriptions, used to apply policy across many of them. Not needed on a free account.
- **Subscription:** the billing and quota boundary. Every resource is created inside one, and costs show on its invoice. A free account gets one subscription.
- **Resource group:** a container for resources with a shared lifecycle, so they can be managed, tagged, permissioned and deleted together. The group has a region, but resources inside it can live in other regions.
- **Resource:** a single service instance, such as a storage account, a Data Factory, a SQL server or a SQL database.

Some resources nest inside others. A **SQL server** is a logical container for databases and holds logins and firewall rules. A **storage account** holds containers, and containers hold blobs. A **Data Factory** holds pipelines, datasets, linked services and triggers.

#### Access control
- Azure uses **role-based access control (RBAC)**: a role is a set of permissions, and a **role assignment** gives a role to a member (user, group or application) at a scope (subscription, resource group or single resource).
- Roles are inherited downward. Owner on a subscription applies to every resource group under it.
- Roles that came up:
    - **Owner:** full access, including granting roles.
    - **Contributor:** manage resources, but cannot grant roles.
    - **Storage Blob Data Reader:** read blob contents only. This is the role Snowflake needs.
- **Managed identities** are identities Azure creates for a resource, so a service like Data Factory can authenticate to others without stored passwords. SQL authentication was used here for simplicity, but managed identities are the better choice in production.

#### Cost controls
- Most resources bill while they exist, even when idle, unless the service can pause. Serverless SQL can pause.
- Deleting the resource group removes its resources and stops the charges.
- A **budget** in Cost Management sends an alert past a set amount. A free account cannot cap spending automatically, so the budget alert is the safety net.

### Azure services in the data path

#### Azure Blob Storage
Stores unstructured files (CSV, Parquet, JSON, images, logs). Closest to **Amazon S3**.
- **Storage account:** top-level unit that holds the data and sets redundancy and access options.
- **Container:** a group of blobs inside an account. Maps to an S3 bucket.
- **Blob:** a file. Most data-engineering files are block blobs.
- **Folders:** Blob Storage is flat. Slashes in a name only look like folders in the portal.
- **Access tiers:** Hot (frequent access), Cool, Archive (cheapest to store, slowest to read).

Containers used in the exercises:

| Container      | Purpose                                   |
| -------------- | ----------------------------------------- |
| `raw`          | The file as received, unchanged           |
| `curated`      | The file after metadata columns are added |
| `snowflake-in` | The file used for the Snowflake exercise  |

#### Azure Data Factory
ADF orchestrates and moves data but stores none itself. It is closest to **AWS Glue** (copy and transform) plus **Step Functions** (orchestration) and **EventBridge** (scheduling).
- No data catalog like the Glue Data Catalog.
- Glue's Spark transformations are closer to ADF Mapping Data Flows or Azure Databricks.

ADF Studio areas:
- **Home:** templates and the Copy Data tool.
- **Author:** pipelines, datasets and linked services.
- **Monitor:** pipeline runs, activity runs and trigger runs.
- **Manage:** linked services, integration runtimes, triggers and Git settings.

#### Azure SQL Database
Managed relational database based on SQL Server. Equivalent of **Amazon RDS** for SQL Server (RDS also offers PostgreSQL and MySQL).
- **Logical server:** holds logins, firewall rules and one or more databases. Not a virtual machine.
- **Database:** holds tables, views and procedures.
- **Compute tiers:** provisioned (fixed capacity) or serverless (scales, and can pause when idle). Serverless bills compute only while running.
- **Authentication:** SQL authentication (login and password) or Microsoft Entra authentication. SQL authentication here.
- **Firewall:** only listed IP addresses can connect, plus Azure services if that setting is on.

### Mapping from AWS to Azure

| AWS                            | Azure                                   | Notes                                           |
| ------------------------------ | --------------------------------------- | ----------------------------------------------- |
| S3                             | Blob Storage                            | Buckets become containers                       |
| Glue (ETL and copy)            | Data Factory (Copy, Mapping Data Flows) | Glue also has a catalog, which ADF lacks        |
| Step Functions and EventBridge | Data Factory pipelines and triggers     | ADF covers orchestration and scheduling         |
| RDS                            | Azure SQL Database                      | Serverless tier is closest to Aurora Serverless |
| IAM roles                      | RBAC roles and managed identities       | Scopes replace resource-policy style            |
| Secrets Manager                | Azure Key Vault                         | Stores connection secrets                       |

### Data Factory building blocks
- **Linked service:** the connection definition. Answers "where is the data?" (a storage account, a SQL database).
- **Dataset:** a named pointer to data inside a linked service, such as a file path or table. Holds the format details (delimiter, header row, encoding). Answers "what is the data?"
- **Activity:** one step. Copy moves data, Delete removes it, Lookup and Get Metadata read information, If Condition branches.
- **Pipeline:** a group of activities run as one workflow. Arrows set order and conditions: green (on success), red (on failure), grey (on completion), blue (on skip).
- **Trigger:** starts a pipeline. Types: manual, schedule, storage event, tumbling window.
- **Parameters and expressions:** pipelines and datasets take parameters. Expressions start with `@`, e.g. `@utcnow()` for the current time and `@pipeline().RunId` for the run ID.
- **System variables:** values ADF provides. `$$FILEPATH` in a Copy activity gives the source file path. It is a Copy-activity variable, written without `@`.

The **Copy Data tool** is a wizard that creates the linked services, datasets, activity and pipeline in one go. Building a pipeline by hand makes it clearer how the pieces connect.

### Setup in Azure
Names used, all in one resource group so cleanup is a single delete:
- **Resource group:** `rg-dataday1`.
- **Budget:** Cost Management > Budgets, $10 monthly with an 80% alert to email.
- **Storage account:** `stday1container`, same region, LRS. Containers: `raw`, `curated`, `snowflake-in`.
- **SQL server and database:** server `sqlsrv-day1-learning` (name must be globally unique), database `sqldb-day1`, SQL authentication with admin `sqladmin`. Serverless compute, auto-pause after 60 minutes.
- **SQL firewall:** Networking > allow Azure services and resources, and add the client IP.
- **Data Factory:** `adfLearning`, version V2, Git configured later.

Target table, created from the database's Query editor:
```sql
DROP TABLE IF EXISTS dbo.stg_data;

CREATE TABLE dbo.stg_data (
    id              NVARCHAR(20)  NOT NULL,
    rated           NVARCHAR(10),
    created_at      BIGINT,
    last_move_at    BIGINT,
    turns           INT,
    victory_status  NVARCHAR(20),
    winner          NVARCHAR(10),
    increment_code  NVARCHAR(20),
    white_id        NVARCHAR(50),
    white_rating    INT,
    black_id        NVARCHAR(50),
    black_rating    INT,
    moves           NVARCHAR(MAX),
    opening_eco     NVARCHAR(10),
    opening_name    NVARCHAR(300),
    opening_ply     INT,
    source_file     NVARCHAR(500),
    load_ts         DATETIME2,
    run_id          NVARCHAR(100)
);
```

### Quickstart copy pipeline
Followed Microsoft's [Get started and try out your first Data Factory pipeline](https://learn.microsoft.com/en-us/azure/data-factory/quickstart-get-started).
- Studio > Home > Ingest > Copy Data tool, task set to **Run once now**.
- Source: the sample file from the quickstart. Destination: Azure Blob Storage container.
- The wizard creates the pipeline. Author > **Debug**, then **Publish all**.
- Monitor > Pipeline runs shows status, duration and rows copied.
### Copying between Blob Storage and Azure SQL
Pipeline `pl_lichess_raw_to_sql` has two Copy activities
#### Linked services
- `ls_blob`: the storage account.
- `ls_sql`: server `sqlsrv-day1-learning.database.windows.net`, database `sqldb-day1`, SQL authentication as `sqladmin`.
- Test connection on both before creating. A failing `ls_sql` test usually means the SQL server firewall.

#### Activity 1: `cp_raw_to_curated`
- **Source:** dataset `ds_raw_csv` (Blob, DelimitedText, linked service `ls_blob`, file in `raw`). First row as header, column delimiter set to **Tab** on the dataset's Connection tab.
- **Additional columns** on the source add lineage metadata:

| Name          | Value                 | Purpose              |
| ------------- | --------------------- | -------------------- |
| `source_file` | `$$FILEPATH` (no `@`) | The source file path |
| `load_ts`     | `@utcnow()`           | The load timestamp   |
| `run_id`      | `@pipeline().RunId`   | The pipeline run ID  |

- **Sink:** dataset `ds_curated_csv` (Blob, DelimitedText, `curated` container, file `curated_output.csv`). Header on, delimiter Tab.
- **Mapping:** Import schemas. Expect 19 columns (16 from the file, 3 metadata). Delete any blank or stray column.

#### Activity 2: `cp_curated_to_sql`
- Linked to activity 1 with the green (on success) arrow, so it only runs if the first copy succeeds.
- **Source:** `ds_curated_csv`, first row as header.
- **Sink:** dataset `ds_sql_stg` (Azure SQL Database, `ls_sql`, table `dbo.stg_data`). Table option **None**, since the table already exists.
- **Mapping:** Import schemas. Columns map by name, so check all 19 map correctly.

#### Verification
```sql
SELECT COUNT(*) AS row_count FROM dbo.stg_data;

SELECT TOP 10 id, rated, white_rating, opening_name, source_file, load_ts, run_id
FROM dbo.stg_data;
```
Row count should equal the data rows in the file (header excluded), and the metadata columns should be filled on every row.

#### Issues to check
- **Every row in one column:** one of the three DelimitedText datasets still has a comma delimiter. Check the Connection tab on each.
- **Mapping errors:** Import schemas again.
- **Conversion errors:** a value does not fit its column type. The error message names the row and column.

### Loading from Blob Storage into Snowflake
Snowflake reads cloud files through a chain of objects: the **storage integration** sets up trust, the **stage** points to the location, the **file format** says how to parse, and **COPY INTO** loads the table. Setup statements run as `ACCOUNTADMIN` (the trial default).

#### 1. Tenant ID
Microsoft Entra ID > Overview > copy the Tenant ID.

#### 2. Storage integration
```sql
CREATE OR REPLACE STORAGE INTEGRATION azure_int
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'AZURE'
  ENABLED = TRUE
  AZURE_TENANT_ID = '<your-tenant-id>'
  STORAGE_ALLOWED_LOCATIONS = ('azure://<storage-account>.blob.core.windows.net/snowflake-in/');
```
It records which tenant and location Snowflake may use. No keys or SAS tokens appear in the SQL.

#### 3. Consent details
```sql
DESC STORAGE INTEGRATION azure_int;
```
Two values matter in the output: `AZURE_CONSENT_URL` and `AZURE_MULTI_TENANT_APP_NAME` (e.g. `SnowflakePACIntegration_abc123`).
#### 4. Consent and confirming the app
- Open `AZURE_CONSENT_URL`, sign in as the owner of the Azure subscription and accept. This registers Snowflake's app in the Azure directory.
- Confirm in Entra ID > Enterprise applications > All applications, searching for the app name (or the part before the underscore).
#### 5. Role assignment
Storage account > Access Control (IAM) > Add role assignment > **Storage Blob Data Reader**, with the Snowflake app as the member. Read-only, and it can take a minute or two to take effect.
#### 6. Stage and file format
```sql
CREATE OR REPLACE STAGE azure_stage
  URL = 'azure://<storage-account>.blob.core.windows.net/snowflake-in/'
  STORAGE_INTEGRATION = azure_int;

CREATE OR REPLACE FILE FORMAT tsv_format
  TYPE = CSV
  FIELD_DELIMITER = ','
  SKIP_HEADER = 1
  NULL_IF = ('', 'NULL');
```
#### 7. Target table
```sql
CREATE OR REPLACE TABLE games_stg (
  id VARCHAR, rated VARCHAR, created_at NUMBER, last_move_at NUMBER,
  turns NUMBER, victory_status VARCHAR, winner VARCHAR, increment_code VARCHAR,
  white_id VARCHAR, white_rating NUMBER, black_id VARCHAR, black_rating NUMBER,
  moves VARCHAR, opening_eco VARCHAR, opening_name VARCHAR, opening_ply NUMBER,
  load_ts TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  source_file VARCHAR
);
```
#### 8. List the stage
```sql
LIST @azure_stage;
```
`games_small.csv` (header plus about 20 rows of the full file, uploaded to `snowflake-in`) should show up. If it does not, or there is an access error, the role assignment is missing or incomplete.

#### 9. Load
```sql
COPY INTO games_stg (id, rated, created_at, last_move_at, turns, victory_status, winner,
                     increment_code, white_id, white_rating, black_id, black_rating,
                     moves, opening_eco, opening_name, opening_ply, source_file)
FROM (
  SELECT $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16,
         METADATA$FILENAME
  FROM @azure_stage
)
FILE_FORMAT = (FORMAT_NAME = tsv_format)
ON_ERROR = 'ABORT_STATEMENT';
```
- The SELECT maps file columns by position (`$1` to `$16`).
- `METADATA$FILENAME` records the source file on each row.
- `ON_ERROR = 'ABORT_STATEMENT'` stops the load at the first bad row.

#### 10. Verify
```sql
SELECT COUNT(*) FROM games_stg;

SELECT id, white_rating, opening_name, source_file, load_ts
FROM games_stg
LIMIT 10;
```
Running COPY INTO again loads zero rows: Snowflake's load history records each loaded file and skips it next time, which prevents duplicates.

### Scheduling and late-arriving files

#### Schedule trigger
- `trg_hourly`: Manage > Triggers > New, type **Schedule**, recurrence every 1 hour, start a few minutes out, activated, then Publish all.
- Firing history: Monitor > Trigger runs.
- A running trigger keeps firing and billing until stopped (Triggers > select it > Stop).

#### What happens when the file is late
Timeline:
- 02:00: the scheduled run fires and `raw` is empty.
- 02:15: the file lands in `raw`.
- 03:00: the next run finds it and loads it.

The load is an hour late but nothing is lost. Things that can still go wrong:
- The run finds no file and fails, so someone has to notice and act.
- The run starts while the file is still uploading and loads a partial file.
- Downstream jobs run on stale data and raise no error.

#### Options for late files
- **Storage event trigger:** starts the pipeline when a blob is created. Best when arrival time is unpredictable.
- **Tumbling window trigger:** fixed time windows with retries and dependency waits. Best for regular batches that must not be missed.
- **Wait-and-check:** a Get Metadata activity checks for the file and an Until loop retries until it appears or a timeout passes, with a failure alert at the timeout. Best when the file has a known deadline.
- **Retry and alerting:** retries on the activity, and failures routed to an Azure Monitor alert.

## Azure Reflection 
The core concepts of cloud, IAM, services, and things like that did feel synonymous. I was able to find corollaries of various services of AWS in Azure - Glue + Step Function became ADF, S3 became Blob Storage, and Redshift became Azure SQL. I now know how to do the work that I can do in AWS, in Azure, too. The fundamentals remains the same across the cloud boundaries, however there can be some gaps in exactly what AWS offers vs what Azure offers, or atleast in the length and breadth I have gone through.

What did not carry over feels like bit of personal snag or opinion, I felt AWS's hierarchy and setup is a lot more simpler and organized. I did not exactly get the 1:1 for IAM across these two. I feel that remains a gap that I will have to further prod upon. I also feel lack of certain services like EMR or Aurora, but that just might be lack of exposure on my part.
