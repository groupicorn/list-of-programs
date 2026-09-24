# Groupicorn program directory data

This repository is the source of truth for Groupicorn's U.S. IOP/PHP discovery
catalog. It contains human-edited source JSON, generated state JSON, and local
provider images. The first goal is nationwide breadth: up to nine plausible
search-discovered results for every defined area.

Discovery coverage is intentionally broader than verification. A result found
on Google, Bing, Maps, a directory, Reddit, or a sponsored page may be recorded
as a discovery lead when it clearly names an IOP/PHP program in the requested
state or area. A discovery lead is not a ranking, clinical recommendation,
admission promise, or confirmation of current availability.

## Repository layout

```text
source/areas/<state>.json       Areas, neighbors, metadata, research queues
source/providers/<state-code>/*.json
                                Provider/location candidates
source/coverage.json            Optional area priorities and thresholds
images/<state-code>/*.png       Local provider assets for promoted records
programs/<state>.json           Generated runtime data
tools/directory.py              Compiler, validator, and coverage CLI
featuredPrograms.json           Separate curated homepage snapshot
```

Edit `source/` and `images/`, then run the compiler. Never hand-edit
`programs/*.json`.

## Search-first workflow

For each city, metro, county, or other area, search several variants:

```text
[city] IOP
[city] PHP
[city] intensive outpatient program
[city] mental health IOP
[city] addiction IOP
[county] behavioral health day treatment
```

Use Google, Bing, or another major search engine. Review the first 10 result
pages, or all available pages when an engine exposes fewer. If the interface
returns a flat result list, review about the first 100 distinct results. Record
plausible local provider/program names until the area has nine distinct groups
or the results repeat. Do not spend the initial pass on exhaustive source
comparison, logo cleanup, phone calls, or intake research.

For each lead, preserve the result URL, query, search engine, date, visible
city/address, apparent care level, and uncertainty. Put unresolved leads in
`research_queue` or mark them `discovery_lead`/`pending` in source. Deduplicate
obvious branches and repeats. Exclude only clear mismatches such as virtual-only
results when local care is required, out-of-state results, ordinary therapy, or
inpatient/residential-only services.

## Discovery versus publication

The directory has three practical stages:

1. **Discovery lead** — plausible result found by search.
2. **Source candidate** — provider/location details captured, with follow-up
   still needed.
3. **Publication-ready** — satisfies the current compiler's source gates.

The compiler currently requires an active location with both a program source
URL and an address source URL before it enters a generated shortlist. Do not
invent missing URLs or hand-edit generated output. If the product should display
raw discovery leads before verification, add a separate compiler/schema change;
the source queue already provides a place to preserve them.

Keep physical addresses, care levels, populations, and operating status scoped
to what the source actually says. Do not infer availability, quality, insurance
acceptance, or clinical outcomes. Do not store patient information or copied
reviews.

## Generated data and validation

```sh
./directory build <state>
./directory validate <state>
./directory coverage
jq empty programs/*.json
git diff --check
```

For compiler or shared-schema changes:

```sh
./directory build
python3 -m unittest discover -s tests -v
```

Generated shortlists remain local-first, neighbor-aware, deduplicated by
provider group, and limited to nine entries. The nine-result discovery target
is a breadth metric; it does not mean the area has nine verified operating
programs. Preserve stable IDs, use the actual physical address for
`primary_area_id`, and leave logos and deep verification for later cleanup
passes. Do not commit or push unless explicitly requested.
