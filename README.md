# Groupicorn program directory data

This repository is the source of truth for Groupicorn's state-level IOP/PHP directory data and local provider-logo assets. The web and iOS applications discover state JSON files and images from here; a new state should not require application source-code changes.

## Repository layout

```text
programs/<state>.json          State directory data
images/<state-code>/*.png      Local provider-logo assets
featuredPrograms.json          Separate curated homepage snapshot
```

Each state directory keeps its geography and prepared results in one JSON file. The established top-level collections are:

- `metadata` — research date, scope, policies, and summaries.
- `providers` — provider identity and deduplication information.
- `locations` — exact treatment locations and evidence.
- `areas` — editorial search catchments and explicit neighbors.
- `area_matches` — candidate matches for each area.
- `shortlists` — prepared display results, normally up to nine distinct provider groups per area.

Areas are editorial travel/search buckets, not claims about municipal boundaries, driving time, eligibility, availability, or clinical quality. Local matches come before explicitly declared neighbors. Provider branches are deduplicated with `provider_dedupe_group_id`; the directory is not a ranking.

`featuredPrograms.json` is a separate homepage display list migrated from older web data. The canonical research directories live under `programs/`. Do not update the featured snapshot as part of an ordinary state-directory change unless the task explicitly includes homepage curation.

## Adding or updating a state

1. Inspect the target JSON, a comparable state, current repository guidance, and the consuming web/iOS paths before editing.
2. Preserve stable provider, location, and area IDs and unrelated records.
3. Verify the same provider, treatment site, care level, population, and current operating evidence before publishing a location.
4. Put geography in the state's `areas` collection. Use the actual treatment address for `primary_area_id`; use `area_matches` and `shortlists` for declared neighboring coverage.
5. Add genuine official PNG logos under the correct lowercase state-code directory. A published `logo_url` must resolve to the exact local file, including case; do not rely on a remote URL or guessed filename.
6. Recalculate shortlist references, ordering, counts, and coverage statuses, then validate the JSON and changed assets.

Prefer metadata titles in the form `Groupicorn <State> IOP/PHP research directory`. Existing files may use older titles or represent incomplete research; do not rewrite unrelated records merely to normalize them.

## Consumer integration

The generic consumers are expected to enumerate `programs/*.json` and derive their state index, state pages, filters, and metadata from those files. Cities and areas are filters within a state page; they do not automatically become city-specific routes or SEO pages.

When the sibling repositories are present, their resource links should resolve to this repository:

```text
web/public/assets/iop_php_logos -> ../../../list-of-programs/images
ios_app/Groupicorn/Resources/programs -> ../../../list-of-programs/programs
ios_app/Groupicorn/Resources/program-images -> ../../../list-of-programs/images
```

Web and iOS must present the same prepared area results. Prefer consuming `shortlists` directly. If a client derives results from `area_matches`, it must preserve local-first ordering, neighbor labels, provider-group deduplication, stable `display_order`, and the nine-entry limit. A client that only filters `locations` by `primary_area_id` is incompatible with the directory semantics and should be fixed or reported; the data should not be weakened to hide the mismatch.

## Validation

At minimum, before handing off a change:

```sh
jq empty programs/*.json
git diff --check
```

Also verify that every changed `logo_url` resolves to a real PNG in `images/`, every referenced provider/location/area ID exists, every location has the correct two-letter `state_code`, and every shortlist contains no duplicate provider group and no more than nine entries. When web and iOS are available, build/check them and confirm the new state appears in the generated web directory index and that both resource trees resolve the JSON and PNG links.

Research records are public-facing data. Keep claims sourced and scoped, preserve uncertainty, do not store sensitive patient information, and do not present the directory as clinical advice or a promise of admission.
