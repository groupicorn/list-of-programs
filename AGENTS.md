# Instructions for `list-of-programs`

## Scope

This repository contains Groupicorn's canonical state-directory JSON and local PNG logo assets. Keep changes repository-native and data-focused.

- Normal directory work may modify only `programs/<state>.json` and required files under `images/<lowercase-state-code>/`.
- Do not add React screens, Swift cases, routes, sitemap entries, generated app files, dependencies, or lockfile changes here.
- `featuredPrograms.json` is a separate curated homepage snapshot. Leave it unchanged unless the request explicitly includes homepage curation.
- Do not commit or push unless explicitly requested.

## Before editing

Read this file, the root `README.md`, the target state JSON, one or two comparable state files, and the relevant consumer/schema conventions when available. Check the worktree first and preserve unrelated changes.

For research updates, use current public sources. Treat earlier assistant output, search rankings, review counts, snippets, and remembered provider facts as discovery leads rather than evidence. Verify the exact provider, treatment address, IOP/PHP service, population, modality, and operating status.

## Data invariants

- Preserve stable provider, location, and area IDs. Do not silently delete, repurpose, or duplicate treatment locations.
- Keep the established top-level collections: `metadata`, `providers`, `locations`, `areas`, `area_matches`, and `shortlists`.
- Every `location` needs a valid two-letter `state_code` matching the actual treatment state. Postal city and editorial area are different concepts.
- Assign `primary_area_id` from the real treatment address. Neighbor coverage must use explicit `areas[].neighbor_area_ids` and `match_type`; do not invent distance or commute claims.
- Shortlists are prepared directory results, not clinical rankings: local first, explicit neighbors second, deduplicated by `provider_dedupe_group_id`, stable `display_order`, and at most nine entries per area.
- Prefer `shortlists` as the canonical prepared result. Keep `area_matches` complete enough for any compatible client that derives the same result.
- Every newly published provider needs a verified official local PNG. A `logo_url` must resolve exactly to the tracked PNG path, including directory, filename, and case. Keep the source/provenance URL separately where supported.
- Do not turn a contact form into confirmed availability, a review into a clinical outcome, or a directory listing into proof of current admission eligibility.

## Generic consumers

Adding a state must require zero web or iOS source-code edits. The generic consumers enumerate the JSON files and derive their state index and pages automatically. If a consumer requires a new hardcoded state case, route, screen, or sitemap entry, report that as a compatibility defect instead of adding a data-side workaround.

Cities and neighborhoods added to a state JSON appear as area filters within the state page. They do not create city-specific web routes unless the application contract is intentionally changed elsewhere.

When sibling repositories are available, check that:

1. The web build discovers the new JSON in its generated directory index and state output.
2. The web resolves all referenced local logo paths and applies the prepared shortlist semantics.
3. iOS resource links resolve `programs/` JSON and `program-images/` PNG assets.
4. iOS consumes `shortlists`/`area_matches`; filtering only by `primary_area_id` is not sufficient because it drops declared neighboring candidates.

## Validation and handoff

Run checks proportional to the change, at least:

```sh
jq empty programs/*.json
git diff --check
```

Inspect changed PNGs with an image/file validator. Confirm referenced IDs, exact-case asset paths, shortlist counts, provider-group uniqueness, and derived counts. Run consumer builds/resource checks when those repositories are available; otherwise state that they were not run. Report actual commands, failures, pending logos, unresolved evidence, and remaining research gaps. Never claim statewide re-verification after a city-only update.
