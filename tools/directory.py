#!/usr/bin/env python3
"""Build, validate, and inspect Groupicorn directory data.

Canonical inputs live under source/ and images/. The JSON files under programs/
are deterministic, checked-in publication artifacts. This module intentionally
uses only the Python standard library so a fresh clone can run it immediately.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
PROGRAMS_DIR = ROOT / "programs"
SOURCE_DIR = ROOT / "source"
AREAS_DIR = SOURCE_DIR / "areas"
PROVIDERS_DIR = SOURCE_DIR / "providers"
IMAGES_DIR = ROOT / "images"
GENERATED_AREA_FIELDS = {
    "local_location_count",
    "local_provider_group_count",
    "candidate_provider_group_count",
    "shortlisted_count",
    "in_area_shortlisted_count",
    "neighbor_shortlisted_count",
    "gap_to_nine",
    "local_gap_to_nine",
    "coverage_status",
    "adult_mental_health_candidates",
}
STATE_CODES = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "newHampshire": "NH", "newJersey": "NJ", "newMexico": "NM", "newYork": "NY",
    "northCarolina": "NC", "northDakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhodeIsland": "RI", "southCarolina": "SC",
    "southDakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA", "westVirginia": "WV",
    "wisconsin": "WI", "wyoming": "WY",
}
READY_PROGRAM_STATUSES = {
    "program_claim_found",
    "verified",
    "verified_exact_site",
    "exact_site_verified",
}
EXCLUDED_STATUSES = {"closed", "excluded", "rejected", "virtual_only"}


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def state_path(state: str) -> Path:
    candidate = PROGRAMS_DIR / (state if state.endswith(".json") else f"{state}.json")
    if candidate.exists():
        return candidate
    matches = sorted(PROGRAMS_DIR.glob("*.json"))
    by_lower = {path.stem.lower(): path for path in matches}
    try:
        return by_lower[state.removesuffix(".json").lower()]
    except KeyError as exc:
        raise SystemExit(f"Unknown state file: {state}") from exc


def state_stem(state: str) -> str:
    return state_path(state).stem


def state_code_for(stem: str, data: dict[str, Any] | None = None) -> str:
    if stem in STATE_CODES:
        return STATE_CODES[stem]
    if data:
        for area in data.get("areas", []):
            if area.get("state_code"):
                return str(area["state_code"]).upper()
        for location in data.get("locations", []):
            if location.get("state_code"):
                return str(location["state_code"]).upper()
    raise SystemExit(f"Cannot determine state code for {stem}")


def source_area_path(stem: str) -> Path:
    return AREAS_DIR / f"{stem}.json"


def active_location(location: dict[str, Any]) -> bool:
    status_values = {
        str(location.get("publication_status", "")).lower(),
        str(location.get("research_status", "")).lower(),
        str(location.get("verification_status", "")).lower(),
    }
    return not status_values.intersection(EXCLUDED_STATUSES)


def publication_ready(location: dict[str, Any]) -> bool:
    if not active_location(location):
        return False
    logo_url = str(location.get("logo_url", ""))
    if not logo_url or not png_is_valid(ROOT / logo_url):
        return False
    explicit = location.get("publication_ready")
    if explicit is not None:
        return bool(explicit)
    program_status = str(location.get("program_site_verification_status", "")).lower()
    verification_status = str(location.get("verification_status", "")).lower()
    if program_status or verification_status:
        return program_status in READY_PROGRAM_STATUSES or verification_status in READY_PROGRAM_STATUSES
    return bool(location.get("program_source_url") and location.get("address_source_url"))


def source_area_data(stem: str) -> dict[str, Any]:
    path = source_area_path(stem)
    if not path.exists():
        raise SystemExit(
            f"No canonical area source for {stem}. Run './directory seed {stem}' "
            "to migrate an existing generated file, or add source/areas/<state>.json."
        )
    data = read_json(path)
    if isinstance(data, list):
        return {"state_file": stem, "state_code": state_code_for(stem), "areas": data}
    if not isinstance(data, dict) or not isinstance(data.get("areas"), list):
        raise SystemExit(f"Invalid area source shape: {path}")
    return data


def source_provider_data(stem: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    directory = PROVIDERS_DIR / state_code_for(stem).lower()
    if not directory.exists():
        raise SystemExit(f"No provider source directory: {directory}")
    providers: list[dict[str, Any]] = []
    locations: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        data = read_json(path)
        if not isinstance(data, dict):
            raise SystemExit(f"Provider source must be an object: {path}")
        provider = data.get("provider")
        if provider is None:
            provider = {key: value for key, value in data.items() if key != "locations"}
        if not isinstance(provider, dict) or not provider.get("provider_id"):
            raise SystemExit(f"Provider source lacks provider_id: {path}")
        providers.append(copy.deepcopy(provider))
        for location in data.get("locations", []):
            if not isinstance(location, dict):
                raise SystemExit(f"Location must be an object: {path}")
            record = copy.deepcopy(location)
            record.setdefault("provider_id", provider["provider_id"])
            locations.append(record)
    return providers, locations


def clean_area(area: dict[str, Any]) -> dict[str, Any]:
    return {key: copy.deepcopy(value) for key, value in area.items() if key not in GENERATED_AREA_FIELDS}


def clean_provider(provider: dict[str, Any], locations: list[dict[str, Any]]) -> dict[str, Any]:
    result = copy.deepcopy(provider)
    result.pop("locations", None)
    result.pop("location_count", None)
    result["location_count"] = len(locations)
    return result


def location_sort_key(location: dict[str, Any]) -> tuple[Any, ...]:
    return (
        location.get("editorial_order", 10**9),
        str(location.get("provider_name", "")).casefold(),
        str(location.get("location_name", "")).casefold(),
        str(location.get("location_id", "")),
    )


def candidate_for_area(
    area: dict[str, Any],
    locations_by_area: dict[str, list[dict[str, Any]]],
    area_by_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    local = [location for location in locations_by_area.get(area["area_id"], []) if publication_ready(location)]
    neighbor: list[dict[str, Any]] = []
    for neighbor_id in area.get("neighbor_area_ids", []):
        if neighbor_id not in area_by_id:
            continue
        neighbor.extend(
            location for location in locations_by_area.get(neighbor_id, []) if publication_ready(location)
        )
    return sorted(local, key=location_sort_key), sorted(neighbor, key=location_sort_key)


def match_record(
    area: dict[str, Any], location: dict[str, Any], match_type: str, order: int,
    area_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    actual_area = area_by_id[location["primary_area_id"]]
    record: dict[str, Any] = {
        "state_code": location.get("state_code", area.get("state_code")),
        "area_id": area["area_id"],
        "area_name": area["name"],
        "region": area.get("region", ""),
        "location_id": location["location_id"],
        "provider_id": location["provider_id"],
        "dedupe_group_id": location.get("provider_dedupe_group_id", location["provider_id"]),
        "provider_name": location.get("provider_name", ""),
        "location_name": location.get("location_name", ""),
        "street_address": location.get("street_address", ""),
        "city": location.get("city", ""),
        "postal_code": location.get("postal_code", ""),
        "match_type": match_type,
        "actual_area_id": actual_area["area_id"],
        "actual_area_name": actual_area.get("name", ""),
        "care_focus": location.get("care_focus", ""),
        "care_levels_claimed": location.get("care_levels_claimed", location.get("care_levels", "")),
        "age_group": location.get("age_group", location.get("age_groups", "")),
        "selected": True,
        "display_order": order,
        "selection_basis": (
            "Local physical-address match selected before explicitly declared neighbors."
            if match_type == "local"
            else "Explicit one-hop neighbor match selected after local candidates."
        ),
        "program_source_url": location.get("program_source_url", ""),
        "address_source_url": location.get("address_source_url", ""),
        "evidence_status": location.get("evidence_status", ""),
        "notes": location.get("notes", ""),
    }
    return record


def build_state(stem: str) -> dict[str, Any]:
    area_source = source_area_data(stem)
    providers, locations = source_provider_data(stem)
    state_code = str(area_source.get("state_code") or state_code_for(stem)).upper()
    areas = [clean_area(area) for area in area_source["areas"]]
    area_by_id = {area["area_id"]: area for area in areas}
    if len(area_by_id) != len(areas):
        raise SystemExit(f"Duplicate area_id in source/areas/{stem}.json")
    provider_by_id = {provider["provider_id"]: provider for provider in providers}
    if len(provider_by_id) != len(providers):
        raise SystemExit(f"Duplicate provider_id in source/providers/{state_code.lower()}")
    locations_by_area: dict[str, list[dict[str, Any]]] = defaultdict(list)
    locations_by_provider: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for location in locations:
        location.setdefault("state_code", state_code)
        if location.get("state_code", "").upper() != state_code:
            raise SystemExit(f"Location {location.get('location_id')} has the wrong state_code")
        if location.get("provider_id") not in provider_by_id:
            raise SystemExit(f"Location {location.get('location_id')} references an unknown provider")
        provider = provider_by_id[location["provider_id"]]
        location.setdefault("provider_name", provider.get("provider_name", ""))
        location.setdefault("provider_dedupe_group_id", provider.get("dedupe_group_id", location["provider_id"]))
        location.setdefault("logo_url", provider.get("logo_url", ""))
        if location.get("primary_area_id") not in area_by_id:
            raise SystemExit(f"Location {location.get('location_id')} references an unknown area")
        locations_by_area[location["primary_area_id"]].append(location)
        locations_by_provider[location["provider_id"]].append(location)
    for area in areas:
        for neighbor_id in area.get("neighbor_area_ids", []):
            if neighbor_id not in area_by_id:
                raise SystemExit(f"Area {area['area_id']} references unknown neighbor {neighbor_id}")
            if neighbor_id == area["area_id"]:
                raise SystemExit(f"Area {area['area_id']} cannot neighbor itself")

    matches: list[dict[str, Any]] = []
    shortlists: list[dict[str, Any]] = []
    generated_areas: list[dict[str, Any]] = []
    target_default = 9
    for area in areas:
        local_locations = [location for location in locations_by_area.get(area["area_id"], []) if active_location(location)]
        local_groups = {
            location.get("provider_dedupe_group_id", location["provider_id"]) for location in local_locations
        }
        candidate_local, candidate_neighbors = candidate_for_area(area, locations_by_area, area_by_id)
        candidates = candidate_local + candidate_neighbors
        selected: list[tuple[dict[str, Any], str]] = []
        seen_groups: set[str] = set()
        for location, match_type in [(item, "local") for item in candidate_local] + [
            (item, "neighbor") for item in candidate_neighbors
        ]:
            group = location.get("provider_dedupe_group_id", location["provider_id"])
            if group in seen_groups or len(selected) >= int(area.get("target_provider_count", target_default)):
                continue
            seen_groups.add(group)
            selected.append((location, match_type))
        for index, (location, match_type) in enumerate(selected, start=1):
            row = match_record(area, location, match_type, index, area_by_id)
            matches.append(row)
            shortlists.append(copy.deepcopy(row))
        local_selected = sum(1 for _, match_type in selected if match_type == "local")
        neighbor_selected = len(selected) - local_selected
        target = int(area.get("target_provider_count", target_default))
        total_selected = len(selected)
        coverage_status = (
            "9_available_locally" if local_selected >= target
            else "9_available_with_neighbors" if total_selected >= target
            else "research_gap"
        )
        generated = copy.deepcopy(area)
        generated.update({
            "local_location_count": len(local_locations),
            "local_provider_group_count": len(local_groups),
            "candidate_provider_group_count": len({
                location.get("provider_dedupe_group_id", location["provider_id"]) for location in candidates
            }),
            "shortlisted_count": total_selected,
            "in_area_shortlisted_count": local_selected,
            "neighbor_shortlisted_count": neighbor_selected,
            "gap_to_nine": max(target - total_selected, 0),
            "local_gap_to_nine": max(target - local_selected, 0),
            "coverage_status": coverage_status,
        })
        generated_areas.append(generated)

    generated_providers = []
    for provider in providers:
        generated_providers.append(clean_provider(provider, locations_by_provider[provider["provider_id"]]))

    metadata = copy.deepcopy(area_source.get("metadata", {}))
    metadata.setdefault("snapshot_date", "")
    metadata.setdefault("title", f"Groupicorn {stem} IOP/PHP research directory")
    metadata["generation_note"] = (
        "Generated from source/areas and source/providers by tools/directory.py; "
        "edit canonical source files rather than this artifact."
    )
    output: dict[str, Any] = {
        "metadata": metadata,
        "providers": generated_providers,
        "locations": locations,
        "areas": generated_areas,
        "area_matches": matches,
        "shortlists": shortlists,
    }
    if "research_queue" in area_source:
        output["research_queue"] = copy.deepcopy(area_source["research_queue"])
    return output


def seed_state(stem: str, force: bool = False) -> None:
    source_area = source_area_path(stem)
    source_provider_dir = PROVIDERS_DIR / state_code_for(stem).lower()
    if (source_area.exists() or source_provider_dir.exists()) and not force:
        raise SystemExit(f"Canonical source already exists for {stem}; use --force only for a deliberate reseed")
    generated = read_json(state_path(stem))
    areas = [clean_area(area) for area in generated.get("areas", [])]
    area_payload = {
        "schema_version": 1,
        "state_file": stem,
        "state_code": state_code_for(stem, generated),
        "metadata": generated.get("metadata", {}),
        "areas": areas,
    }
    if "research_queue" in generated:
        area_payload["research_queue"] = generated["research_queue"]
    write_json(source_area, area_payload)
    providers_by_id = {provider["provider_id"]: copy.deepcopy(provider) for provider in generated.get("providers", [])}
    locations_by_provider: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for location in generated.get("locations", []):
        locations_by_provider[location["provider_id"]].append(copy.deepcopy(location))
    for provider_id, provider in providers_by_id.items():
        provider.pop("location_count", None)
        payload = provider
        payload["locations"] = locations_by_provider[provider_id]
        write_json(source_provider_dir / f"{provider_id}.json", payload)
    print(f"Seeded {stem}: {source_area.relative_to(ROOT)} and {len(providers_by_id)} provider fragments")


def compile_state(stem: str, check: bool = False) -> bool:
    generated = build_state(stem)
    destination = state_path(stem)
    if check:
        current = read_json(destination)
        same = current == generated
        if not same:
            print(f"OUT OF DATE {destination.relative_to(ROOT)}")
        else:
            print(f"OK {destination.relative_to(ROOT)}")
        return same
    write_json(destination, generated)
    print(f"Built {destination.relative_to(ROOT)}")
    return True


def iter_program_paths(state: str | None = None) -> Iterable[Path]:
    if state:
        yield state_path(state)
    else:
        yield from sorted(PROGRAMS_DIR.glob("*.json"))


def png_is_valid(path: Path) -> bool:
    try:
        data = path.read_bytes()
    except OSError:
        return False
    return len(data) >= 24 and data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR"


def validate_state(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = read_json(path)
    except Exception as exc:  # pragma: no cover - exercised by malformed input
        return [f"{path}: invalid JSON: {exc}"]
    required = {"metadata", "providers", "locations", "areas", "area_matches", "shortlists"}
    missing = required.difference(data)
    if missing:
        errors.append(f"{path}: missing top-level collections: {', '.join(sorted(missing))}")
        return errors
    stem = path.stem
    expected_code = state_code_for(stem, data)
    providers = data["providers"]
    locations = data["locations"]
    areas = data["areas"]
    area_by_id = {item.get("area_id"): item for item in areas}
    provider_by_id = {item.get("provider_id"): item for item in providers}
    location_by_id = {item.get("location_id"): item for item in locations}
    for label, records, key in (("provider", providers, "provider_id"), ("location", locations, "location_id"), ("area", areas, "area_id")):
        ids = [record.get(key) for record in records]
        if None in ids or len(ids) != len(set(ids)):
            errors.append(f"{path}: duplicate or missing {label} IDs")
    for location in locations:
        location_id = location.get("location_id", "<missing>")
        if location.get("state_code", "").upper() != expected_code:
            errors.append(f"{path}: {location_id} has state_code {location.get('state_code')!r}, expected {expected_code}")
        if location.get("provider_id") not in provider_by_id:
            errors.append(f"{path}: {location_id} references unknown provider")
        if location.get("primary_area_id") not in area_by_id:
            errors.append(f"{path}: {location_id} references unknown area")
        logo = location.get("logo_url", "")
        if logo:
            asset = ROOT / logo
            if not asset.is_file() or not png_is_valid(asset):
                errors.append(f"{path}: invalid or missing location logo {logo}")
    for provider in providers:
        logo = provider.get("logo_url", "")
        if logo:
            asset = ROOT / logo
            if not asset.is_file() or not png_is_valid(asset):
                errors.append(f"{path}: invalid or missing provider logo {logo}")
    for area in areas:
        area_id = area.get("area_id", "<missing>")
        neighbors = area.get("neighbor_area_ids", [])
        for neighbor in neighbors:
            if neighbor == area_id or neighbor not in area_by_id:
                errors.append(f"{path}: invalid neighbor {neighbor!r} on {area_id}")
    for collection_name in ("area_matches", "shortlists"):
        rows_by_area: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in data[collection_name]:
            area_id = row.get("area_id")
            location_id = row.get("location_id")
            if area_id not in area_by_id:
                errors.append(f"{path}: {collection_name} references unknown area {area_id}")
            if location_id not in location_by_id:
                errors.append(f"{path}: {collection_name} references unknown location {location_id}")
            rows_by_area[area_id].append(row)
        for area_id, rows in rows_by_area.items():
            groups = [row.get("dedupe_group_id") for row in rows]
            if collection_name == "shortlists" and len(groups) != len(set(groups)):
                errors.append(f"{path}: {collection_name} duplicates provider groups in {area_id}")
            orders = [row.get("display_order") for row in rows]
            if collection_name == "shortlists" and len(rows) > 9:
                errors.append(f"{path}: {collection_name} has more than nine rows in {area_id}")
            if collection_name == "shortlists" and orders != list(range(1, len(rows) + 1)):
                errors.append(f"{path}: {collection_name} display_order is not contiguous in {area_id}")
            for row in rows:
                if row.get("match_type") == "neighbor" and row.get("actual_area_id") not in area_by_id[area_id].get("neighbor_area_ids", []):
                    errors.append(f"{path}: neighbor row {row.get('location_id')} is not an explicit neighbor of {area_id}")
    return errors


def validate(state: str | None = None) -> int:
    errors: list[str] = []
    paths = list(iter_program_paths(state))
    legacy_count = 0
    for path in paths:
        if source_area_path(path.stem).exists():
            errors.extend(validate_state(path))
        else:
            # Legacy state files are intentionally not treated as generated
            # until their source fragments exist. Keep this command useful
            # during the incremental migration instead of reporting known
            # pre-compiler conventions as thousands of new failures.
            try:
                legacy = read_json(path)
                if not isinstance(legacy, dict):
                    errors.append(f"{path}: top level must be an object")
                else:
                    required = {"metadata", "providers", "locations", "areas", "area_matches", "shortlists"}
                    missing = required.difference(legacy)
                    if missing:
                        errors.append(f"{path}: missing top-level collections: {', '.join(sorted(missing))}")
                    else:
                        legacy_count += 1
            except Exception as exc:  # pragma: no cover - malformed legacy file
                errors.append(f"{path}: invalid JSON: {exc}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        print(f"Validation failed: {len(errors)} error(s) across {len(paths)} state file(s)", file=sys.stderr)
        return 1
    generated_count = len(paths) - legacy_count
    suffix = f"; {legacy_count} legacy state file(s) pending source migration" if legacy_count else ""
    print(f"Validation passed: {generated_count} generated state file(s){suffix}")
    return 0


def area_count(area: dict[str, Any]) -> int:
    return int(area.get("shortlisted_count", 0))


def coverage() -> int:
    manifest_path = SOURCE_DIR / "coverage.json"
    manifest = read_json(manifest_path) if manifest_path.exists() else {"metros": []}
    found: set[tuple[str, str]] = set()
    states: dict[str, dict[str, Any]] = {}
    for path in sorted(PROGRAMS_DIR.glob("*.json")):
        data = read_json(path)
        states[path.stem] = data
        found.update((path.stem, area.get("area_id")) for area in data.get("areas", []))
    rows: list[tuple[int, str, str, int, str]] = []
    for item in manifest.get("metros", []):
        stem = item["state_file"]
        area_id = item["area_id"]
        data = states.get(stem)
        area = next((candidate for candidate in data.get("areas", []) if candidate.get("area_id") == area_id), None) if data else None
        count = area_count(area) if area else 0
        target = int(item.get("target", 9))
        priority = 0 if area is None or count == 0 else 1 if count < 3 else 2 if count < 5 else 3 if count < target else 4
        status = "missing geography" if area is None else f"{count}/{target}"
        rows.append((priority, item.get("display_name", area_id), stem, count, status))
    rows.sort(key=lambda row: (row[0], row[1].casefold()))
    for priority, name, stem, count, status in rows:
        label = f"P{priority}" if priority < 4 else "OK"
        print(f"{label:<3} {name:<24} {stem:<16} {status}")
    print(f"\nCoverage manifest: {len(rows)} priority metro(s); source/coverage.json is the editable geography queue.")
    return 0


def build_all() -> int:
    stems = sorted(path.stem for path in AREAS_DIR.glob("*.json"))
    if not stems:
        raise SystemExit("No canonical area sources found under source/areas/")
    ok = True
    for stem in stems:
        ok = compile_state(stem) and ok
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="directory")
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser("build", help="Generate checked-in programs JSON")
    build_parser.add_argument("state", nargs="?", help="State file stem; omit to build all canonical states")
    compile_parser = subparsers.add_parser("compile", help="Alias for build")
    compile_parser.add_argument("state")
    compile_parser.add_argument("--check", action="store_true", help="Check without writing")
    seed_parser = subparsers.add_parser("seed", help="Migrate an existing generated state into source fragments")
    seed_parser.add_argument("state")
    seed_parser.add_argument("--force", action="store_true")
    validate_parser = subparsers.add_parser("validate", help="Validate generated JSON and logo references")
    validate_parser.add_argument("state", nargs="?")
    subparsers.add_parser("coverage", help="Print the committed priority metro coverage queue")
    subparsers.add_parser("research-queue", help="Alias for coverage")
    args = parser.parse_args(argv)
    if args.command == "seed":
        seed_state(state_stem(args.state), force=args.force)
    elif args.command in {"build", "compile"}:
        if args.command == "build" and not args.state:
            raise SystemExit(build_all())
        stem = state_stem(args.state)
        success = compile_state(stem, check=getattr(args, "check", False))
        if not success:
            raise SystemExit(1)
    elif args.command == "validate":
        raise SystemExit(validate(args.state))
    else:
        raise SystemExit(coverage())


if __name__ == "__main__":
    main()
