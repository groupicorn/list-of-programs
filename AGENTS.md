# Instructions for `list-of-programs`

## Scope

This repository contains Groupicorn's canonical research source JSON, generated state-directory JSON, and local PNG logo assets. The generated files and images are published under `https://romeo.groupicorn.com/data/` and consumed there by web and iOS. Keep changes repository-native and data-focused; clients must not require a checkout of this repository at build or deploy time.

The national goal is to bring every state to California-like geographic breadth
and usefulness. Treat California's area granularity and research breadth as the
benchmark; during source migration, its current generated publication-ready
counts may themselves still require improvement. Do not treat nine shortlist
entries in one area as state completion: research should cover major metros,
secondary cities, and realistic regional hubs, and should retain additional
verified providers when the local market supports them.

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

## Coverage-driven work selection

The long-term objective is nationwide California-like breadth: practical
geographic coverage, provider diversity, exact physical treatment locations,
evidence-backed IOP/PHP claims, and durable local PNG assets. California is the
model for geographic granularity and research breadth; do not assume every
current California record is publication-ready during canonical-source
migration.

`./directory coverage` is the authoritative progress report. `needs.txt` is
only a checked-in generated snapshot of the `NEEDS_WORK` rows and must never be
hand-curated or treated as a separate source of truth.

When the user asks to continue coverage work without naming a state or area,
select work from current coverage rather than choosing a state arbitrarily or
simply taking the first alphabetical line in `needs.txt`.

Use this priority order:

1. Work higher `pass_priority` areas first. An explicit priority override in
   `source/coverage.json` outranks ordinary areas.
2. Within the same priority, prefer the area closest to its configured local
   launch threshold: smallest positive
   `minimum_local - local_count`. This normally means a 2-local area needing
   one additional publication-ready provider before a 1-local or 0-local area.
3. If additional strategic ordering is important, encode it in
   `source/coverage.json` rather than relying on agent judgment or alphabetical
   order.
4. Do not continue adding providers to an area that has already met its
   configured threshold while higher-priority `NEEDS_WORK` areas remain,
   unless the user explicitly asks for that area.

Before searching for new providers in the selected area, run:

```sh
./directory explain <state> <area>
```

Prefer completing existing canonical candidates before discovering new ones.
A candidate that already has the correct physical site may only need current
program-level evidence, a verified official local PNG, or another publication
gate resolved.

After each useful batch, regenerate and validate from canonical source:

```sh
./directory build
./directory validate
./directory coverage | grep '^NEEDS_WORK' > needs.txt
git diff --check
```

`./directory build` with no state argument rebuilds every canonical state.
`needs.txt` should be reproducible by the command above; if regenerating it
without other source changes produces a diff, investigate the generated state
data rather than manually editing `needs.txt`.

### Coverage maturity stages

Coverage work happens in stages. Do not treat the first passing threshold as
national completion.

**Stage 1 — Eliminate `NEEDS_WORK`.**
Bring every practical area to its configured `minimum_local`, normally three
local publication-ready provider groups. This is the nationwide launch floor.

**Stage 2 — Move `LAUNCH` areas to `GOOD`.**
After higher-priority `NEEDS_WORK` gaps are exhausted, deepen areas that only
meet the launch floor. The default `GOOD` threshold is five local
publication-ready provider groups. Prefer areas closest to becoming `GOOD`
first unless `source/coverage.json` says otherwise.

**Stage 3 — Build useful depth.**
After geographic areas have good local coverage, work toward the configured
total-choice target, normally nine distinct useful provider groups. Neighbor
results may contribute where appropriate; state-level fallback results are
display alternatives and do not count as local or neighboring coverage.

**Stage 4 — Audit geography and state maturity.**
A state is not mature merely because every currently defined area is `GOOD`.
Review its geography against major metros, secondary population centers, and
realistic regional hubs. Add missing areas when meaningful population centers
or geographic regions are absent. Dense markets may also justify retaining
more than nine verified provider groups in canonical source even though the
prepared shortlist is capped.

A mature state should therefore have:

* a practical statewide geography skeleton rather than one strong metro;
* no obvious major metro or regional-hub gaps;
* at least launch-level local coverage throughout that geography;
* stronger local depth in markets that support it;
* diverse provider groups rather than duplicated branches;
* exact physical locations;
* current, source-backed IOP/PHP evidence;
* valid official local PNG assets; and
* additional verified canonical providers retained when useful beyond the
  current shortlist limit.

The progression is therefore:

```text
0–2 local -> launch threshold -> GOOD local depth -> total-choice depth
-> geography audit -> mature state
```

Continue using the repository's generated metrics to decide the next
incremental task until every state approaches the same breadth and usefulness,
rather than declaring a state complete from a single successful shortlist.

### Migration versus real coverage changes

Canonical-source migration can make reported coverage temporarily decrease.
This is expected when older records fail stricter publication gates such as
site-specific IOP/PHP evidence or a valid local PNG.

Do not restore old counts by weakening publication rules, copying legacy
shortlists, inventing evidence, or counting fallback areas as local coverage.
Use `./directory explain` to identify why candidates fail publication and
improve the canonical evidence instead.

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
./directory build
./directory validate
./directory coverage | grep '^NEEDS_WORK' > needs.txt
jq empty programs/*.json
git diff --check
```

Inspect changed PNGs with an image/file validator. Confirm referenced IDs, exact-case asset paths, shortlist counts, provider-group uniqueness, and derived counts. Run consumer builds/resource checks when those repositories are available; otherwise state that they were not run. Report actual commands, failures, pending logos, unresolved evidence, and remaining research gaps. Never claim statewide re-verification after a city-only update.
