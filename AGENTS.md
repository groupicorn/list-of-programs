# Instructions for `list-of-programs`

## Purpose

This repository holds Groupicorn's U.S. IOP/PHP discovery data, generated state
JSON, and local image assets. The first product goal is broad coverage: find up
to nine plausible search results for every defined area in every state. Those
results are discovery leads, not clinical rankings or promises of availability.

Search breadth comes first. Verification, exact-site cleanup, logos, and
current-status review are later passes. Do not block a state's discovery pass
because every lead is not yet perfect.

## Files and boundaries

- Edit `source/areas/*.json`, `source/providers/<lowercase-state-code>/*.json`,
  `source/coverage.json`, and `images/<lowercase-state-code>/`.
- `programs/<state>.json` is generated. Run `./directory build`; never hand-edit
  it.
- Leave `featuredPrograms.json`, app code, routes, dependencies, and lockfiles
  alone unless explicitly requested.
- Preserve stable provider IDs, location IDs, area IDs, filenames, and published
  URL paths.
- Do not commit or push unless explicitly requested.

## Search-first workflow

1. Check `git status`, read the target state's source and generated JSON, and
   run `./directory next` or `./directory coverage` to choose the next area.
2. Search Google, Bing, or another major engine using the city/metro/county:
   `[city] IOP`, `[city] PHP`, `[city] intensive outpatient program`,
   `[city] mental health IOP`, `[city] addiction IOP`, and similar variants.
3. Paginate Google deliberately. For each query, open the normal result page
   and then request the next pages with `start=0,10,20,...,90` (or use the
   engine's Next control). Record the exact query, engine, page offset, and
   discovery date with every lead; include the offset in the `--query` value
   when using `./directory add-lead` (for example, `Google start=20`).
   Review up to ten pages per query, or all available pages when an engine
   exposes fewer. If the interface returns a flat result list, review roughly
   the first 100 distinct results and record the page/offset convention used.
   Continue across query variants until the area has nine distinct groups or
   several consecutive pages only repeat known results. A state-wide breadth
   pass may continue across areas until roughly 100 plausible distinct leads
   are captured. Do not treat a result count as coverage until exact duplicates
   and obvious mismatches have been removed.
4. Deduplicate obvious branches and exact repeats. Exclude only obvious
   virtual-only, out-of-state, non-IOP/PHP, and inpatient/residential-only
   results during discovery.
5. Store incomplete results as `discovery_lead` or `pending` records and put
   unresolved follow-up in the area's `research_queue`. Record the result URL,
   search query, search engine and page offset, date, visible city/address, and
   uncertainty. Do not assign an area only because the result mentions that
   area; use the visible treatment address when one is available and queue
   the location when it is not.
6. Rebuild and validate the affected state.

A search result can be counted toward the initial discovery target without being
called verified. Never fabricate an address, care level, logo, population,
operating status, or availability claim to fill a slot.

## Source semantics

Use the existing source model:

- `source/areas/<state>.json` contains editorial areas, neighbors, and queues.
- `source/providers/<state-code>/*.json` contains provider/location candidates.
- `programs/<state>.json` contains compiler output for clients.

Keep these states distinct:

- `discovery_lead`: plausible search result;
- `source_candidate`: partly captured provider/location needing follow-up;
- `publication-ready`: satisfies the current compiler's source gates.

The current compiler publishes an active `google_discovery_lead` when it has
one non-empty source URL. Its address URL and logo may be empty. Other statuses
still require both program and address source URLs. Do not invent URLs or hand
edit generated JSON.

Keep real physical addresses when known and leave unknown values unknown. Use
the actual treatment address for `primary_area_id`; do not place a provider in
an area merely because its search result mentions that area. Deduplicate branches
with the existing provider dedupe group. Do not store patient identities,
health histories, copied reviews, or intake information.

## Logos and later cleanup

Logo collection is not part of the initial search pass. When promoting a
candidate for publication, use a genuine provider-controlled PNG under the
correct state directory and preserve its source URL. Never invent or redesign a
logo. Queue missing logos, exact-address checks, current program checks, and
operating-status checks for later.

## Validation

Run the smallest relevant checks after each batch:

```sh
./directory build <state>
./directory validate <state>
jq empty programs/*.json
git diff --check
```

For compiler or shared-schema changes also run:

```sh
./directory build
python3 -m unittest discover -s tests -v
```

Report actual commands, new discovery leads, existing duplicates, queued
uncertainties, generated coverage, and failures. Do not claim that nine search
leads are nine verified operating programs.
