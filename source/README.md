# Canonical source data

Git is the source of truth for this directory. Human-edited research facts live
under `source/`; official local PNGs live under `images/`. The files under
`programs/` are generated publication artifacts, checked into Git so a clone is
immediately usable and so R2 publishing does not need a build-time checkout of
another repository.

## Provider fragments

Use one JSON file per provider under `source/providers/<state-code>/`. A file
contains the provider fields and an embedded `locations` array. Researchers may
edit provider identity, exact treatment addresses, care-level evidence,
population, source URLs, and verification notes. They must not edit shortlist or
coverage totals.

The compiler accepts the existing repository vocabulary, including
`program_site_verification_status`. A location is eligible for a generated
shortlist only when its exact-site program status is verified (for example
`program_claim_found` or `verified`) and its local logo exists. Unverified and
logo-pending research can remain in the source fragment without being presented
as a ready directory option.

## Area files

`source/areas/<state-file>.json` contains the editorial geography, explicit
one-hop practical neighbors (not merely statewide or same-state adjacency),
optional state-level `fallback_area_ids`, state metadata, and an optional
research queue. Fallbacks are labeled separately and do not count toward
coverage totals. The compiler derives local/neighbor/fallback matches,
provider-group deduplication, ordering, nine-entry caps, counts, gaps, and
coverage status.

Provider-specific verification tasks should use `provider_id` and, when
appropriate, `location_id`. Older name-based tasks are still recognized during
migration; builds warn and omit a task when its provider now has complete
program, address, and local-logo evidence.

## Workflow

```sh
./directory seed indiana       # one-time migration of an existing state
./directory compare indiana    # must report Unexpected changes: 0 before research edits
./directory build indiana      # source -> programs/indiana.json
./directory validate indiana
./directory coverage
./directory explain texas el-paso
```

`coverage` enumerates every area in every generated state. The optional
`source/coverage.json` file contains only priority and threshold overrides;
unlisted areas use a local launch floor of three and a total prepared-choice
target of nine. Use `explain` to see why a source location is not publishable,
including pending program evidence, exclusion statuses, and missing local PNGs.

Commit source JSON, required PNGs, and the regenerated `programs/<state>.json`
together. CI should run `./directory build` and fail when the generated diff is
not clean, then run `./directory validate`. Only image files (`.png`, `.jpg`,
`.jpeg`, `.webp`, `.svg`) may exist under `images/`.
