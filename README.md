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

Use Google, Bing, or another major search engine. In Google, start at the
normal results URL and walk the result pages with `start=0,10,20,...,90` (or
the Next control). Keep the exact query, engine, page offset, and discovery
date with each captured result; include the offset in `--query` when using the
CLI. Do not assume that one page or one query is representative. Review up to 10
pages per query, or all available pages when an engine exposes fewer. If the
interface returns a flat result list, review about the first 100 distinct
results and document the page/offset convention used. Continue across city,
county, IOP, PHP, mental-health, and substance-use variants until the area has
nine distinct groups or several consecutive pages only repeat known results.
For a state-wide breadth pass, continue across areas until roughly 100
plausible distinct leads are captured. Deduplicate exact URLs, branches, and
provider groups before counting coverage. Do not spend the initial pass on
exhaustive source comparison, logo cleanup, phone calls, or intake research.

For each lead, preserve the result URL, query, search engine, page offset, date,
visible city/address, apparent care level, and uncertainty. Put unresolved
leads in `research_queue` or mark them `discovery_lead`/`pending` in source.
Deduplicate obvious branches and repeats. Assign the lead to the area of its
actual treatment address when known; otherwise queue the location for follow-up.
Exclude only clear mismatches such as virtual-only results when local care is
required, out-of-state results, ordinary therapy, or inpatient/residential-only
services.

For a fast Google capture, use the queue helper; it writes the source record and
rebuilds the state automatically:

```sh
./directory add-lead wisconsin wi_madison "Provider Name" "https://example.com/iop" \
  --query "Google start=0 | Madison Wisconsin IOP" --city Madison \
  --address "123 Main Street"
```

Only the name, valid area, and result URL are required. Treat the generated row
as a discovery lead, not a verified operating program.

## Discovery versus publication

The directory has three practical stages:

1. **Discovery lead** — plausible result found by search.
2. **Source candidate** — provider/location details captured, with follow-up
   still needed.
3. **Publication-ready** — satisfies the current compiler's source gates.

The compiler publishes an active `google_discovery_lead` when it has one valid
website source URL. A site root may be `https://foo.com` or `https://foo.com/`;
deeper paths must end in `/`, and document URLs such as PDFs are not valid
program URLs. Its address URL and logo may be empty. A queue item with
`queue_type: google_discovery_lead` is materialized the same way, so a new lead
does not need a provider fragment before it appears in the generated directory.
Invalid leads remain queued for follow-up. Other statuses still require a valid
program source URL and an address source URL. Do not invent missing URLs or
hand-edit generated output.

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
