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
one-hop practical neighbors (not merely statewide or same-state adjacency), state metadata, and optional research queue. The compiler
derives local/neighbor matches, provider-group deduplication, ordering, nine-
entry caps, counts, gaps, and coverage status.

## Workflow

```sh
./directory seed indiana       # one-time migration of an existing state
./directory build indiana      # source -> programs/indiana.json
./directory validate indiana
./directory coverage
```

Commit source JSON, required PNGs, and the regenerated `programs/<state>.json`
together. CI should run `./directory build` and fail when the generated diff is
not clean, then run `./directory validate`.
