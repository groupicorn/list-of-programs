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

    def write_fixture(self, area_ids=("in_indianapolis",), neighbors=None, fallbacks=None, locations=()):
        neighbors = neighbors or {}
        fallbacks = fallbacks or {}
        areas = []
        for area_id in area_ids:
            areas.append({
                "area_id": area_id,
                "state_code": "IN",
                "region": "Test Indiana",
                "name": area_id,
                "neighbor_area_ids": neighbors.get(area_id, []),
                "fallback_area_ids": fallbacks.get(area_id, []),
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
            if spec.get("with_sources", True):
                location["program_source_url"] = "https://example.com/program"
                location["address_source_url"] = "https://example.com/address"
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

    def test_fallback_results_are_labeled_and_excluded_from_coverage_total(self):
        result = self.build_fixture(
            area_ids=("in_indianapolis", "in_fort_wayne"),
            fallbacks={"in_indianapolis": ["in_fort_wayne"]},
            locations=({
                "location_id": "fallback",
                "provider_id": "fallback-provider",
                "area_id": "in_fort_wayne",
            },),
        )

        rows = [row for row in result["shortlists"] if row["area_id"] == "in_indianapolis"]
        area = next(area for area in result["areas"] if area["area_id"] == "in_indianapolis")
        self.assertEqual("fallback", rows[0]["match_type"])
        self.assertEqual(0, area["shortlisted_count"])
        self.assertEqual(1, area["fallback_shortlisted_count"])

    def test_completed_research_queue_item_is_omitted_from_generated_output(self):
        self.write_fixture(locations=({
            "location_id": "completed",
            "provider_id": "completed-provider",
        },))
        area_path = self.areas_dir / "indiana.json"
        area_source = json.loads(area_path.read_text())
        area_source["research_queue"] = [{
            "queue_type": "verify_program_level",
            "area_id": "in_indianapolis",
            "provider_id": "completed-provider",
            "location_id": "completed",
            "name": "Stale Provider Name",
        }]
        directory.write_json(area_path, area_source)

        result = directory.build_state("indiana")

        self.assertEqual([], result["research_queue"])

    def test_area_scoped_queue_item_does_not_use_another_location(self):
        self.write_fixture(
            area_ids=("in_indianapolis", "in_fort_wayne"),
            locations=(
                {
                    "location_id": "ready-indianapolis",
                    "provider_id": "multi-location-provider",
                    "area_id": "in_indianapolis",
                },
                {
                    "location_id": "pending-fort-wayne",
                    "provider_id": "multi-location-provider",
                    "area_id": "in_fort_wayne",
                    "program_status": "program_claim_pending",
                    "with_sources": False,
                },
            ),
        )
        area_path = self.areas_dir / "indiana.json"
        area_source = json.loads(area_path.read_text())
        area_source["research_queue"] = [
            {
                "queue_type": "verify_program_level",
                "area_id": "in_indianapolis",
                "provider_id": "multi-location-provider",
                "location_id": "",
            },
            {
                "queue_type": "verify_program_level",
                "area_id": "in_fort_wayne",
                "provider_id": "multi-location-provider",
                "location_id": "",
            },
        ]
        directory.write_json(area_path, area_source)

        result = directory.build_state("indiana")

        self.assertEqual(["in_fort_wayne"], [item["area_id"] for item in result["research_queue"]])

    def test_non_image_files_are_rejected(self):
        self.write_fixture(locations=({"location_id": "local", "provider_id": "local-provider"},))
        (self.images_dir / "in" / "notes.json").write_text("{}", encoding="utf-8")

        with self.assertRaisesRegex(SystemExit, "unsupported file under images|Invalid files under images"):
            directory.build_state("indiana")

    def test_legacy_pipe_delimited_neighbors_are_supported(self):
        result = self.build_fixture(
            area_ids=("in_indianapolis", "in_fort_wayne"),
            neighbors={"in_indianapolis": "in_fort_wayne"},
            locations=({
                "location_id": "neighbor",
                "provider_id": "neighbor-provider",
                "area_id": "in_fort_wayne",
            },),
        )

        rows = [row for row in result["shortlists"] if row["area_id"] == "in_indianapolis"]
        self.assertEqual(["neighbor"], [row["location_id"] for row in rows])
        self.assertEqual("neighbor", rows[0]["match_type"])

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

    def test_pending_program_with_sources_is_published(self):
        result = self.build_fixture(locations=({
            "location_id": "pending",
            "provider_id": "pending-provider",
            "program_status": "program_claim_pending",
        },))

        self.assertEqual(["pending"], [row["location_id"] for row in result["shortlists"]])

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

    def test_missing_logo_does_not_block_research_candidate(self):
        result = self.build_fixture(locations=({
            "location_id": "no-logo",
            "provider_id": "no-logo-provider",
            "logo_url": "images/in/missing.png",
        },))

        self.assertEqual(["no-logo"], [row["location_id"] for row in result["shortlists"]])

    def test_verified_program_is_published(self):
        result = self.build_fixture(locations=({
            "location_id": "verified",
            "provider_id": "verified-provider",
        },))

        self.assertEqual(["verified"], [row["location_id"] for row in result["shortlists"]])

    def test_current_source_program_claim_is_published_with_local_logo(self):
        result = self.build_fixture(locations=({
            "location_id": "current-source",
            "provider_id": "current-source-provider",
            "program_status": "current_source_program_claim",
        },))

        self.assertEqual(["current-source"], [row["location_id"] for row in result["shortlists"]])

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
        manifest = {"overrides": [{
            "state_file": "indiana",
            "area_id": "in_indianapolis",
            "minimum_local": 3,
            "pass_priority": 0,
        }]}
        states = {"indiana": {"areas": [{
            "area_id": "in_indianapolis",
            "in_area_shortlisted_count": 3,
            "shortlisted_count": 3,
        }]}}

        row = directory.coverage_rows(manifest, states)[0]

        self.assertEqual("LAUNCH", row["status"])
        self.assertEqual(3, row["local_count"])
        self.assertEqual(3, row["total_count"])
        self.assertFalse(row["needs_work"])
        self.assertEqual(0, row["need"])

    def test_coverage_reports_deficit(self):
        manifest = {"overrides": [{
            "state_file": "indiana",
            "area_id": "in_indianapolis",
            "minimum_local": 5,
        }]}
        states = {"indiana": {"areas": [{
            "area_id": "in_indianapolis",
            "in_area_shortlisted_count": 3,
            "shortlisted_count": 3,
        }]}}

        row = directory.coverage_rows(manifest, states)[0]

        self.assertEqual(2, row["need"])

    def test_next_coverage_prioritizes_p1_deficit_then_ordinary_buckets(self):
        def row(area_id, local_count, minimum_local=3, pass_priority=0):
            need = max(minimum_local - local_count, 0)
            return {
                "area_id": area_id,
                "display_name": area_id,
                "state_file": "indiana",
                "local_count": local_count,
                "total_count": local_count,
                "minimum_local": minimum_local,
                "pass_priority": pass_priority,
                "needs_work": True,
                "need": need,
            }

        rows = directory.next_coverage_rows([
            row("ordinary-one-local", 1),
            row("ordinary-zero-local", 0),
            row("ordinary-two-local", 2),
            row("p1-needs-two", 3, minimum_local=5, pass_priority=1),
            row("p1-needs-one", 4, minimum_local=5, pass_priority=1),
        ])

        self.assertEqual([
            "p1-needs-one",
            "p1-needs-two",
            "ordinary-two-local",
            "ordinary-zero-local",
            "ordinary-one-local",
        ], [item["area_id"] for item in rows])

    def test_coverage_enumerates_areas_not_in_overrides(self):
        manifest = {"overrides": [{
            "state_file": "indiana",
            "area_id": "in_a",
            "minimum_local": 5,
        }]}
        states = {"indiana": {"areas": [
            {"area_id": "in_a", "name": "Area A", "in_area_shortlisted_count": 5, "shortlisted_count": 5},
            {"area_id": "in_b", "name": "Area B", "in_area_shortlisted_count": 1, "shortlisted_count": 9},
        ]}}

        rows = directory.coverage_rows(manifest, states)

        by_id = {row["area_id"]: row for row in rows}
        self.assertEqual({"in_a", "in_b"}, set(by_id))
        self.assertEqual("GOOD", by_id["in_a"]["status"])
        self.assertEqual("NEEDS_WORK", by_id["in_b"]["status"])
        self.assertEqual(9, by_id["in_b"]["total_count"])

    def test_explanation_reports_program_evidence_gate(self):
        reasons = directory.explanation_reasons({
            "program_site_verification_status": "needs_provider_web_confirmation",
            "logo_url": "https://www.google.com/s2/favicons?sz=128&domain_url=https://example.com/",
        })

        self.assertIn("program evidence pending: needs_provider_web_confirmation", reasons)
        self.assertNotIn("missing or invalid local PNG", reasons)

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
