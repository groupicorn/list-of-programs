# Groupicorn program directory data

This repository is the source of truth for Groupicorn's state-level IOP/PHP research data and local provider-logo assets. Human-edited source JSON and PNGs are authoritative in Git. `programs/*.json` is a deterministic generated artifact, also checked into Git for immediate clone usability and publication to `https://romeo.groupicorn.com/data/`; web and iOS clients read the published URLs directly instead of linking, copying, or bundling this repository at build time.

## Repository layout

```text
source/areas/<state>.json       Canonical editorial geography and metadata
source/providers/<state-code>/*.json
                                Canonical provider/location research fragments
source/coverage.json            Optional local-coverage threshold overrides
images/<state-code>/*.png       Canonical local provider-logo assets
programs/<state>.json           Generated, checked-in runtime data
tools/directory.py              Python compiler, validator, and coverage CLI
featuredPrograms.json           Separate curated homepage snapshot
```

Git remains the database. There is no shared SQL service to clone or keep in
sync. A provider researcher can add one fragment without touching another
researcher's fragment; the compiler merges them into the generated state file.

## National quality goal

The goal is to bring every state to the breadth and usefulness of the current
California directory. California is the repository's benchmark for geographic
coverage, provider diversity, exact physical locations, evidence-backed care
levels, and durable local logo assets—not a reason to copy its records or
inflate counts.

The target is a genuinely researched state, not merely one metro with nine
cards. Each state should have a practical geography skeleton, coverage across
major metros and regional hubs, multiple distinct provider groups per area,
and a wider verified source set when the market supports it. The current nine
entry limit is a prepared per-area display contract; it is not a cap on
research, canonical provider records, locations, or future consumer views.

The source/generated boundary is strict:

```sh
./directory build indiana
./directory validate indiana
./directory coverage
./directory explain texas el-paso
```

Edit `source/` and `images/`, then regenerate `programs/`. Never hand-edit a
generated state file. Commit the canonical source, required PNGs, and the
regenerated artifact together. CI should run `./directory build` and fail if
that command changes tracked generated output.

The published layout mirrors the repository layout:

```text
https://romeo.groupicorn.com/data/programs/<state-file>.json
https://romeo.groupicorn.com/data/images/<lowercase-state-code>/<png-file>
https://romeo.groupicorn.com/data/featuredPrograms.json
```

The state JSON files are the required runtime data. `featuredPrograms.json` is required by the current Groupicorn web homepage's curated-logo section; publish it whenever that section is in use. The bucket must allow CORS `GET` and `HEAD` from each Groupicorn client origin, return JSON with `Content-Type: application/json`, and return PNGs with `Content-Type: image/png`. Keep stable filenames and URLs when refreshing data so clients and caches do not break.

Each generated state directory keeps its geography and prepared results in one
JSON file. The established top-level collections are:

- `metadata` — research date, scope, policies, and summaries.
- `providers` — provider identity and deduplication information.
- `locations` — exact treatment locations and evidence.
- `areas` — editorial search catchments and explicit neighbors.
- `area_matches` — candidate matches for each area.
- `shortlists` — prepared display results, normally up to nine distinct provider groups per area. Additional researched providers should remain in canonical source even when they are not selected for the current display shortlist.

Areas are editorial travel/search buckets, not claims about municipal boundaries, driving time, eligibility, availability, or clinical quality. Local matches come before explicitly declared neighbors. Optional `fallback_area_ids` are state-level alternatives, are labeled separately, and do not count toward an area's coverage total. Provider branches are deduplicated with `provider_dedupe_group_id`; the directory is not a ranking.

`featuredPrograms.json` is a separate homepage display list migrated from older web data. The canonical research directories live under `programs/`. Do not update the featured snapshot as part of an ordinary state-directory change unless the task explicitly includes homepage curation.

## Migration gate

For a completely unmigrated legacy state, prove the source round-trip before
research workers change geography or provider records:

```sh
./directory seed STATE
./directory compare STATE
```

The compare report must end with `Unexpected changes: 0`. After that gate,
research workers may edit disjoint provider fragments and the integrating agent
may intentionally update areas or generated output.

`./directory coverage` enumerates every area in every generated state. It uses
`minimum_local` (default `3`) as the launch floor and reports local prepared
groups separately from total prepared choices (default target `9`). Entries in
`source/coverage.json` are overrides for priority or thresholds, not the
national area list. Each unfinished row includes its calculated `NEED` deficit.
Use `./directory next` to select the first unfinished area: explicit P1 areas
come first by smallest deficit, followed by ordinary areas one provider short,
zero-local strategic holes, and the remaining unfinished areas.

`./directory explain STATE [AREA]` reports each canonical source location's
publication decision and the gates that prevented publication, including
program evidence, exclusion status, and missing or invalid local PNG assets.

## Adding or updating a state

1. Inspect the target state's source fragments, generated JSON, a comparable state, current repository guidance, and the consuming web/iOS paths before editing.
2. Preserve stable provider, location, and area IDs and unrelated records.
3. Verify the same provider, treatment site, care level, population, and current operating evidence before publishing a location.
4. Put geography in `source/areas/<state-file>.json`. Use the actual treatment address for `primary_area_id`; the compiler generates `area_matches` and `shortlists` for declared neighboring coverage.
5. Add genuine official PNG logos under the correct lowercase state-code directory. For bucket-native clients, prefer a JSON `logo_url` such as `images/ak/ak-alaska-behavioral-health.png`; clients resolve that path relative to the data root. A published path must resolve to the exact PNG, including case. Do not rely on a guessed filename or an external favicon proxy as the canonical logo source.
6. Run `./directory build <state>` and `./directory validate <state>`; never hand-recalculate generated fields.
7. Run `./directory compare <state>` before accepting a migration; it exits nonzero when provider, location, area, or prepared-shortlist output changes.

Prefer metadata titles in the form `Groupicorn <State> IOP/PHP research directory`. Existing files may use older titles or represent incomplete research; do not rewrite unrelated records merely to normalize them.

## Consumer integration

The generic consumers are expected to enumerate `programs/*.json` in the source/publishing workflow and consume the matching public bucket URL at runtime. They derive state pages, filters, and metadata from those files. Cities and areas are filters within a state page; they do not automatically become city-specific routes or SEO pages.

Web and iOS must present the same prepared area results. Prefer consuming `shortlists` directly. If a client derives results from `area_matches`, it must preserve local-first ordering, neighbor labels, provider-group deduplication, stable `display_order`, and the nine-entry limit. A client that only filters `locations` by `primary_area_id` is incompatible with the directory semantics and should be fixed or reported; the data should not be weakened to hide the mismatch.

## Validation

At minimum, before handing off a change:

```sh
jq empty programs/*.json
git diff --check
```

Also verify that every changed `logo_url` resolves to a real PNG in `images/`, every referenced provider/location/area ID exists, every location has the correct two-letter `state_code`, and every shortlist contains no duplicate provider group and no more than nine entries. After publishing, verify representative `GET` and `HEAD` requests against the matching `https://romeo.groupicorn.com/data/...` URLs. When web and iOS are available, build/check them and confirm the new state appears in each client's directory index and that both clients resolve the JSON and PNG URLs without sibling-repository links.

Research records are public-facing data. Keep claims sourced and scoped, preserve uncertainty, do not store sensitive patient information, and do not present the directory as clinical advice or a promise of admission.

The asset tree is strict: `images/` may contain only `.png`, `.jpg`, `.jpeg`,
`.webp`, and `.svg` files. The compiler and validator reject other files.
Directory provider logos currently have a narrower publication requirement:
`publication_ready()` accepts only a valid local PNG for a logo, even though
the asset tree permits the other common image formats.
