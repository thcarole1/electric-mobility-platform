# 009 - Poi/meteo join: from geographic proximity to an exact key

## Context

ADR-008 anticipated a poi/meteo join based on date and geographic
proximity, since the weather table originally had only one reference
point (central Paris) while each poi has its own precise coordinates.

## Decision

Rather than implementing a geographic distance calculation (for
example haversine in SQL) to reconcile two independent tables after
the fact, the weather API is called directly on the coordinates of
each poi concerned (a sample of 5 poi, randomly selected with a fixed
seed for reproducibility). Each weather row therefore carries an
exact poi_id right from ingestion, removing the need for a proximity
join.

The meteo table uses a composite primary key (poi_id, time), with
poi_id as a foreign key referencing poi(poi_id). The final join
between poi and meteo is an exact join on poi_id, structurally
identical to the one between poi and connections.

Architecture added: common.io.generer_nom_fichier (already
generalized in ADR-007) reused to name each weather extraction per
poi. ingestion.meteo.ingerer_meteo modified to return the generated
file name (str | None rather than None), letting the caller build a
{poi_id: file_name} mapping without reconstructing this information
from the file name (an approach judged fragile and set aside).
cleaning.meteo.assembler_meteo_multi_poi assembles the files from
several poi into a single flat table, reusing extraire_meteo without
modifying it. warehouse.duckdb_loader.charger_meteo_dans_duckdb
orchestrates the creation and loading of the meteo table, separately
from charger_openchargemap_dans_duckdb: two distinct functions per
data source, consistent with the separation already established via
common/io.py, rather than a single function mixing both sources.

## Why

Geographic proximity calculation only has value if the weather points
and the poi are genuinely independent. By choosing to query the
weather API directly at the coordinates of each poi concerned, this
independence disappears: the correspondence becomes trivial and
exact, with no loss of precision compared to a proximity join, which
would have approximated the real position of the poi with the nearest
weather point anyway. This decision was made after several discussions
that explored, then set aside, a temporal key at the poi level (poi
being static entities with no real usage timestamp). The temporal
dimension remains relevant only for a future join between weather and
simulated charging sessions (Phase 2, not built at this stage), not
for the poi/meteo join itself.

## Consequences

This approach does not scale as is to a very large number of poi (one
API call per poi, against a quota of 10,000 requests per day at
Open-Meteo). The sample of 5 poi remains a pedagogical choice for this
stage of the project. If the project ever widens the geographic area
or the number of poi covered by weather, a real proximity join (or a
shared weather grid point system) will become relevant again and will
need to be designed separately.
