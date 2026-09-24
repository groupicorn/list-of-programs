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
`program_site_verification_status`. An active location with
`publication_status`, `research_status`, `verification_status`, or `status` set
to `google_discovery_lead` is eligible for a generated research shortlist when
it has one valid website source URL (`program_source_url` or `source_url`). A
site root may be `https://foo.com` or `https://foo.com/`; deeper paths must end
in `/`, and document URLs such as PDFs are not valid program URLs. Its address
URL and logo may be empty. A `research_queue` item with
`queue_type: google_discovery_lead` is materialized into the same minimal
location shape when it has a name, valid `area_id`, and one valid website
`source_url`; it remains in the queue for later address and current-status
follow-up. Other statuses require a valid program source URL and an address
source URL. Explicitly closed, rejected, virtual-only, or otherwise excluded
records remain out of generated results.

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
program and address source evidence.

## Workflow

```sh
./directory seed indiana       # one-time migration of an existing state
./directory compare indiana    # must report Unexpected changes: 0 before research edits
./directory add-lead wisconsin wi_madison "Provider Name" "https://example.com/iop"
./directory build indiana      # source -> programs/indiana.json
./directory validate indiana
./directory coverage
./directory explain texas el-paso
```

`coverage` enumerates every area in every generated state. The optional
`source/coverage.json` file contains only priority and threshold overrides;
unlisted areas use a local launch floor of three and a total prepared-choice
target of nine. Use `explain` to see why a source location is not included,
including missing source URLs and exclusion statuses. Pending program evidence
and missing local PNGs are surfaced as record-quality follow-up work rather
than removing the physical candidate from coverage.

Commit source JSON, required PNGs, and the regenerated `programs/<state>.json`
together. CI should run `./directory build` and fail when the generated diff is
not clean, then run `./directory validate`. Only image files (`.png`, `.jpg`,
`.jpeg`, `.webp`, `.svg`) may exist under `images/`.
