# 026 - Business restitution: Power BI dashboard and fixing a data type inconsistency

## Context

The entire pipeline built so far (ingestion, transformation,
orchestration, monitoring) produced data usable in SQL via Athena,
with no visual restitution making it directly accessible for business
use. This gap was a limitation of the project: a data pipeline finds
its justification in its final use, not only in its technical
construction.

## Decision

Connection of Power BI Desktop to Athena via a dedicated ODBC driver
(Amazon Athena ODBC 2.x), authenticated with the administrator
account's credentials. Built a two-page dashboard:

- **Overview**: geographic map of charging points, breakdown of
  connector types, key indicators (number of stations, number of
  connectors, average power), interactive filter
- **Availability and power**: operational availability rate
  (computed through a DAX measure rather than a direct aggregation on
  a boolean), average power by connector type, detailed table by
  station

The `.pbix` file is intentionally not versioned in the repository,
since this proprietary binary format can embed cached connection
information; only screenshots document the result.

## Why

Choosing to connect Power BI directly to Athena, rather than exporting
the data to an intermediate format, allows a restitution that reflects
the real, current state of the data lake, with no additional
synchronization step to maintain.

Using a DAX measure for the availability rate, rather than a direct
average-type aggregation on the boolean column `is_operational`, was
necessary because this column type did not lend itself directly to an
average aggregation in the Power BI interface.

## Consequences

### Incident: type inconsistency on `poi_id` in the weather data

The first connection attempt failed with the Athena error
`HIVE_BAD_DATA: Malformed Parquet file`, the `poi_id` column of the
`processed/meteo/meteo.parquet` file being of type `String` while the
schema declared in the Glue Catalog expected `bigint`.

The diagnosis required ruling out several successive hypotheses before
identifying the real cause: neither the weather Lambda function (which
only produces raw JSON, never Parquet), nor a contamination of the
source JSON by the text identifier used to name the files. The actual
cause was in the MWAA DAG (`tache_assemblage_meteo`): the POI/file
correspondence dictionary, passed between Airflow tasks via XCom, is
serialized to JSON by this mechanism, a format in which an object's
keys are necessarily strings. The numeric identifiers used as keys
upstream therefore came back as text once read after this XCom
transit, contaminating the entire schema of the Polars DataFrame built
from this data.

Fixed with an explicit conversion (`int(poi_id)`) in
`assembler_meteo_multi_poi`, along with a test specifically reproducing
this case (a dictionary key provided as a string). The Parquet file
already present on S3 was fixed directly through a one-off script that
read it back and rewrote it with the target type, a full new pipeline
run having been temporarily impossible due to an Open Charge Map API
outage, itself confirmed by similar reports on the service's community
forum.

This incident illustrates a general limitation of distributed
orchestration architectures: an intermediate serialization mechanism
(here XCom) can silently alter a data type with no error ever raised
at transit time, the problem only surfacing later, in a system with
strict schema querying like Athena.

### Additional robustness

On the occasion of this diagnosis, an explicit 30-second `timeout` was
added to the `requests.get` calls of the Open Charge Map and weather
ingestion modules, which lacked one. Without it, a network call left
with no response could block the pipeline's execution indefinitely
with no explicit failure.
