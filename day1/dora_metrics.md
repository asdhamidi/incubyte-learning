# DORA Metrics

A set of standardized indicators that measure how effectively an enterprise builds, deploys, and operates software. They assess delivery performance across two dimensions: throughput, which measures the speed and frequency of software changes, and stability, which measures the frequency of failures and the ability to recover from them.

## Metrics

### Throughput Metrics

Throughput is a measure of how many changes can move through the system over a period of time.

- Change Lead Time: The time it takes for a code change to go from development to production. Shorter lead times indicate faster delivery of features and fixes.
- Deployment Frequency: The number of deployments to production within a given time period. Higher deployment frequency indicates faster delivery of features and fixes.
- Failed Deployment Recovery Time: The time it takes to recover from a deployment that fails and requires immediate intervention. This metric measures the ability to quickly recover from failures and minimize downtime.

### Stability Metrics

Instability is a measure of how well the software deployments go.

- Change Failure Rate: The ratio of deployments that require immediate intervention following a deployment. Likely resulting in a rollback of the changes or a “hotfix” to quickly remediate any issues. This metric measures the stability of the software and the effectiveness of the deployment process.
- Deployment Recovery Rate: The ratio of deployments that are unplanned but happen as a result of an incident in production. This metric measures the ability to recover from failures and minimize downtime.

## DORA in Data Pipeline Context

### Deployment

A deployment in a data pipeline context is an identifiable change release of change to production/qa data or addition or removal of data, data source, data pipeline, or data transformation. It is a change that is deployed to production and is expected to be stable and reliable.

### Change Failure

A change failure in the data context is a deployment that results in data becoming incorrect, incomplete, unavailable, or simple wrong. This can have a cascading effect on downstream systems, so a change failure can also be data pipelines crashing, reports or dashboards being inccorect, unavailable, or down, SLAs not being met or data being lost, or data being corrupted. So, a failure can be something that ran with green but resulted in incorrect data or a failure that resulted in a pipeline crash or data loss.

### Time to Restore

Time to restore in the data context is the time it takes to recover from a change failure and restore the data to a correct, complete, and available state. This can consists of correction of transformation logic, schema changes, data reprocessing, syntactical corrections, configurational changes, or any other changes that are required to restore the data to a correct or expected state.
