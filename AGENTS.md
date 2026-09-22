# Instructions for `list-of-programs`

## Scope

This repository contains Groupicorn's canonical research source JSON, generated state-directory JSON, and local PNG logo assets. The generated files and images are published under `https://romeo.groupicorn.com/data/` and consumed there by web and iOS. Keep changes repository-native and data-focused; clients must not require a checkout of this repository at build or deploy time.

The national goal is to bring every state to the breadth and usefulness of the
current California directory. Treat California as the benchmark for geographic
coverage, provider diversity, exact physical locations, evidence-backed care
levels, and official local logo assets. Do not treat nine shortlist entries in
one area as state completion: research should cover major metros, secondary
cities, and realistic regional hubs, and should retain additional verified
providers when the local market supports them.

- Git-tracked canonical source is `source/areas/*.json`, `source/providers/<lowercase-state-code>/*.json`, `source/coverage.json`, and required files under `images/<lowercase-state-code>/`.
- `programs/<state>.json` is generated and checked into Git for publication and clone usability. Do not hand-edit it; run `./directory build <state>` after changing canonical source.
- CI should run `./directory build` and fail if the generated diff is dirty, then run `./directory validate`.
- Do not add React screens, Swift cases, routes, sitemap entries, generated app files, dependencies, or lockfile changes here.
- `featuredPrograms.json` is a separate curated homepage snapshot. Leave it unchanged unless the request explicitly includes homepage curation.
- Preserve the published URL contract: `programs/<state-file>.json`, `images/<lowercase-state-code>/<png-file>`, and (when homepage curation is enabled) `featuredPrograms.json`.
- Prefer relative bucket-native logo paths such as `images/ak/ak-alaska-behavioral-health.png` in `logo_url`. Treat external favicon URLs as legacy fallback/provenance, not the canonical asset.
- Do not commit or push unless explicitly requested.

## Before editing

Read this file, the root `README.md`, the target state's source fragments and generated JSON, one or two comparable states, and the relevant consumer/schema conventions when available. Check the worktree first and preserve unrelated changes.

For research updates, use current public sources. Treat earlier assistant output, search rankings, review counts, snippets, and remembered provider facts as discovery leads rather than evidence. Verify the exact provider, treatment address, IOP/PHP service, population, modality, and operating status.

## Data invariants

- Preserve stable provider, location, and area IDs. Do not silently delete, repurpose, or duplicate treatment locations.
- Keep the established top-level collections: `metadata`, `providers`, `locations`, `areas`, `area_matches`, and `shortlists`.
- Every `location` needs a valid two-letter `state_code` matching the actual treatment state. Postal city and editorial area are different concepts.
- Assign `primary_area_id` in canonical source from the real treatment address. Neighbor coverage must use explicit source-area neighbors; the compiler generates `match_type`, matches, and shortlists. Do not invent distance or commute claims.
- Shortlists are prepared directory results, not clinical rankings: local first, explicit neighbors second, deduplicated by `provider_dedupe_group_id`, stable `display_order`, and at most nine entries per area.
- The nine-entry shortlist limit is a current consumer display contract, not a research or source-data limit. A dense area may need more than nine discovered or verified provider groups; retain credible additional records in canonical source and do not discard them merely because they are outside the current display shortlist.
- Prefer generated `shortlists` as the canonical prepared result. Keep generated `area_matches` complete enough for any compatible client that derives the same result.
- Every newly published provider needs a verified official local PNG. A `logo_url` must resolve exactly to the tracked PNG path, including directory, filename, and case. Keep the source/provenance URL separately where supported.
- Do not turn a contact form into confirmed availability, a review into a clinical outcome, or a directory listing into proof of current admission eligibility.

## Generic consumers

The published data is designed for generic consumers: a new state should be discoverable from the published program set without a new screen or hardcoded data case. Until the bucket exposes a machine-readable manifest, clients may keep a small routing index for known state slugs; do not duplicate the state records or PNGs into client repositories. If a consumer requires a new hardcoded route or screen, report that as a compatibility defect instead of adding a data-side workaround.

Cities and neighborhoods added to a state JSON appear as area filters within the state page. They do not create city-specific web routes unless the application contract is intentionally changed elsewhere.

When web and iOS are available, check that:

1. The published URL for the new JSON returns valid JSON with CORS `GET`/`HEAD`.
2. The web resolves the published JSON and PNG URLs and applies the prepared shortlist semantics.
3. iOS resolves the same `programs/` JSON and `images/` PNG URLs.
4. iOS consumes `shortlists`/`area_matches`; filtering only by `primary_area_id` is not sufficient because it drops declared neighboring candidates.

## Validation and handoff

Run checks proportional to the change, at least:

```sh
jq empty programs/*.json
git diff --check
```

Inspect changed PNGs with an image/file validator. Confirm referenced IDs, exact-case asset paths, shortlist counts, provider-group uniqueness, and derived counts. Run consumer builds/resource checks when those repositories are available; otherwise state that they were not run. Report actual commands, failures, pending logos, unresolved evidence, and remaining research gaps. Never claim statewide re-verification after a city-only update.
