# 003 - Normalizing the town field from the POI title

## Context

56% of POIs (28/50) had an empty `AddressInfo.Town` field, even
though the town name was often present in `title`, in the format
"Town | Address".

## Decision

Added a `town_normalisee` column: if `town` is empty and `title`
contains the " | " pattern, extract the part before it as a fallback
town. Otherwise, keep `null`. The original `town` column is kept
intact; `town_normalisee` is added as a complement.

## Why

- The " | " pattern is not guaranteed to be universal across all Open
  Charge Map data. Applying the rule only when it is verified avoids
  inventing a town for cases that do not follow this format (for
  example, the "pompidou" POI, intentionally left as null)
- Keeping both columns preserves traceability between source data and
  derived data, rather than overwriting the original information

## Consequences

Any future analysis by town must use `town_normalisee`, not `town`.
If the sample expands to other cities, the rule remains valid without
modification, since it does not depend on the name "Paris".
