import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import directory


class DirectoryFixtureTestCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.programs_dir = self.root / "programs"
        self.source_dir = self.root / "source"
        self.areas_dir = self.source_dir / "areas"
        self.providers_dir = self.source_dir / "providers"
        self.images_dir = self.root / "images"
        for path in (self.programs_dir, self.areas_dir, self.providers_dir / "in", self.images_dir / "in"):
            path.mkdir(parents=True)
        self.patcher = patch.multiple(
            directory,
            ROOT=self.root,
            PROGRAMS_DIR=self.programs_dir,
            SOURCE_DIR=self.source_dir,
            AREAS_DIR=self.areas_dir,
            PROVIDERS_DIR=self.providers_dir,
            IMAGES_DIR=self.images_dir,
        )
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.tempdir.cleanup()

    def write_fixture(self, area_ids=("in_indianapolis",), neighbors=None, locations=()):
        neighbors = neighbors or {}
        areas = []
        for area_id in area_ids:
            areas.append({
                "area_id": area_id,
                "state_code": "IN",
                "region": "Test Indiana",
                "name": area_id,
                "neighbor_area_ids": neighbors.get(area_id, []),
                "target_provider_count": 9,
            })
        directory.write_json(self.areas_dir / "indiana.json", {
            "schema_version": 1,
            "state_file": "indiana",
            "state_code": "IN",
            "metadata": {"title": "Test directory"},
            "areas": areas,
        })

        providers = {}
        for spec in locations:
            provider_id = spec["provider_id"]
            provider = providers.setdefault(provider_id, {
                "provider_id": provider_id,
                "provider_name": spec.get("provider_name", provider_id.title()),
                "dedupe_group_id": spec.get("dedupe_group_id", provider_id),
                "logo_url": f"images/in/{provider_id}.png",
            })
            logo_url = spec.get("logo_url", provider["logo_url"])
            location = {
                "location_id": spec["location_id"],
                "primary_area_id": spec.get("primary_area_id", spec.get("area_id", area_ids[0])),
                "provider_id": provider_id,
                "location_name": spec.get("location_name", spec["location_id"]),
                "provider_name": provider["provider_name"],
                "logo_url": logo_url,
                "program_site_verification_status": spec.get("program_status", "verified"),
                "street_address": "1 Test Street",
                "city": "Indianapolis",
                "state_code": "IN",
            }
            for key in ("publication_status", "research_status", "verification_status", "publication_ready"):
                if key in spec:
                    location[key] = spec[key]
            provider.setdefault("locations", []).append(location)

        for provider_id, provider in providers.items():
            image = self.images_dir / "in" / f"{provider_id}.png"
            image.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01")
            directory.write_json(self.providers_dir / "in" / f"{provider_id}.json", provider)

    def build_fixture(self, **kwargs):
        self.write_fixture(**kwargs)
        return directory.build_state("indiana")


class DirectoryCompilerTests(DirectoryFixtureTestCase):
    def test_seed_build_preserves_shortlists(self):
        before = self.build_fixture(
            area_ids=("in_indianapolis",),
            locations=({"location_id": "local", "provider_id": "local-provider"},),
        )
        directory.write_json(self.programs_dir / "indiana.json", before)
        shutil.rmtree(self.areas_dir)
        shutil.rmtree(self.providers_dir / "in")

        directory.seed_state("indiana")
        after = directory.build_state("indiana")

        self.assertEqual(before, after)

    def test_local_results_come_before_neighbors(self):
        result = self.build_fixture(
            area_ids=("in_indianapolis", "in_fort_wayne"),
            neighbors={"in_indianapolis": ["in_fort_wayne"]},
            locations=(
                {"location_id": "neighbor", "provider_id": "neighbor-provider", "area_id": "in_fort_wayne"},
                {"location_id": "local", "provider_id": "local-provider", "area_id": "in_indianapolis"},
            ),
        )
        rows = [row for row in result["shortlists"] if row["area_id"] == "in_indianapolis"]

        self.assertEqual(["local", "neighbor"], [row["location_id"] for row in rows])
        self.assertEqual(["local", "neighbor"], [row["match_type"] for row in rows])

    def test_same_provider_is_deduped(self):
        result = self.build_fixture(
            locations=(
                {"location_id": "first", "provider_id": "same-provider"},
                {"location_id": "second", "provider_id": "same-provider"},
            ),
        )

        rows = result["shortlists"]
        self.assertEqual(1, len(rows))
        self.assertEqual("same-provider", rows[0]["dedupe_group_id"])

    def test_pending_program_is_not_published(self):
        result = self.build_fixture(locations=({
            "location_id": "pending",
            "provider_id": "pending-provider",
            "program_status": "program_claim_pending",
        },))

        self.assertEqual([], result["shortlists"])

    def test_closed_program_is_not_published(self):
        result = self.build_fixture(locations=({
            "location_id": "closed",
            "provider_id": "closed-provider",
            "publication_status": "closed",
        },))

        self.assertEqual([], result["shortlists"])

    def test_virtual_only_program_is_not_published(self):
        result = self.build_fixture(locations=({
            "location_id": "virtual",
            "provider_id": "virtual-provider",
            "publication_status": "virtual_only",
        },))

        self.assertEqual([], result["shortlists"])

    def test_missing_logo_is_not_published(self):
        result = self.build_fixture(locations=({
            "location_id": "no-logo",
            "provider_id": "no-logo-provider",
            "logo_url": "images/in/missing.png",
        },))

        self.assertEqual([], result["shortlists"])

    def test_verified_program_is_published(self):
        result = self.build_fixture(locations=({
            "location_id": "verified",
            "provider_id": "verified-provider",
        },))

        self.assertEqual(["verified"], [row["location_id"] for row in result["shortlists"]])

    def test_duplicate_location_id_fails(self):
        self.write_fixture(locations=(
            {"location_id": "duplicate", "provider_id": "first-provider"},
            {"location_id": "duplicate", "provider_id": "second-provider"},
        ))

        with self.assertRaisesRegex(SystemExit, "Duplicate location_id"):
            directory.build_state("indiana")

    def test_unknown_area_fails(self):
        self.write_fixture(locations=({
            "location_id": "unknown-area",
            "provider_id": "provider",
            "primary_area_id": "in_missing",
        },))

        with self.assertRaisesRegex(SystemExit, "unknown area"):
            directory.build_state("indiana")

    def test_unknown_provider_fails(self):
        self.write_fixture(locations=({
            "location_id": "unknown-provider",
            "provider_id": "provider",
        },))
        provider_path = self.providers_dir / "in" / "provider.json"
        provider = json.loads(provider_path.read_text())
        provider["locations"][0]["provider_id"] = "in_missing"
        directory.write_json(provider_path, provider)

        with self.assertRaisesRegex(SystemExit, "unknown provider"):
            directory.build_state("indiana")

    def test_build_is_deterministic(self):
        kwargs = {
            "area_ids": ("in_indianapolis", "in_fort_wayne"),
            "neighbors": {"in_indianapolis": ["in_fort_wayne"]},
            "locations": (
                {"location_id": "neighbor", "provider_id": "neighbor-provider", "area_id": "in_fort_wayne"},
                {"location_id": "local", "provider_id": "local-provider", "area_id": "in_indianapolis"},
            ),
        }
        first = self.build_fixture(**kwargs)
        second = directory.build_state("indiana")

        self.assertEqual(first, second)

    def test_coverage_uses_minimum(self):
        manifest = {"metros": [{
            "state_file": "indiana",
            "area_id": "in_indianapolis",
            "minimum": 3,
            "pass_priority": 0,
        }]}
        states = {"indiana": {"areas": [{"area_id": "in_indianapolis", "shortlisted_count": 3}]}}

        row = directory.coverage_rows(manifest, states)[0]

        self.assertEqual("3/3", row["status"])
        self.assertFalse(row["needs_work"])

    def test_coverage_uses_pass_priority(self):
        manifest = {"metros": [
            {"state_file": "indiana", "area_id": "in_a", "minimum": 3, "pass_priority": 2},
            {"state_file": "indiana", "area_id": "in_b", "minimum": 3, "pass_priority": 0},
        ]}
        states = {"indiana": {"areas": [
            {"area_id": "in_a", "shortlisted_count": 0},
            {"area_id": "in_b", "shortlisted_count": 0},
        ]}}

        rows = directory.coverage_rows(manifest, states)

        self.assertEqual([0, 2], [row["pass_priority"] for row in rows])
        self.assertEqual(["in_b", "in_a"], [row["area_id"] for row in rows])


class CanonicalIndianaTests(unittest.TestCase):
    def test_indianapolis_does_not_gain_fort_wayne(self):
        result = directory.build_state("indiana")
        indy = [row for row in result["shortlists"] if row["area_id"] == "in_indianapolis"]

        self.assertNotIn(
            "parkview-behavioral-health-fort_wayne",
            {row["location_id"] for row in indy},
        )
        self.assertEqual("Central Indiana", next(
            area["region"] for area in result["areas"] if area["area_id"] == "in_indianapolis"
        ))


if __name__ == "__main__":
    unittest.main()
