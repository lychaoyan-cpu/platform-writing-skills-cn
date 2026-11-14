from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "behavioral_fixture_checker", ROOT / "scripts" / "check_behavioral_fixture.py"
)
assert SPEC and SPEC.loader
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)

FACT_PACKET_SCHEMA = json.loads(
    (ROOT / "schemas" / "fact-packet.schema.json").read_text(encoding="utf-8")
)
OUTPUT_CONTRACT_SCHEMA = json.loads(
    (ROOT / "schemas" / "output-contract.schema.json").read_text(encoding="utf-8")
)
PLATFORMS = json.loads((ROOT / "config" / "platforms.json").read_text(encoding="utf-8"))["platforms"]
FIXTURES = ROOT / "tests" / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def check(scenario: dict) -> list[str]:
    return CHECKER.check_scenario(
        scenario, FACT_PACKET_SCHEMA, OUTPUT_CONTRACT_SCHEMA, PLATFORMS
    )


class BehavioralFixtureTests(unittest.TestCase):
    def test_bundled_scenario_passes(self) -> None:
        self.assertEqual([], check(load_fixture("behavioral-scenario-sandblasting.json")))

    def test_scenario_covers_three_platforms_from_one_packet(self) -> None:
        scenario = load_fixture("behavioral-scenario-sandblasting.json")
        platforms = [draft["platform_id"] for draft in scenario["drafts"]]
        self.assertEqual(["wechat", "zhihu", "xiaohongshu"], platforms)
        packet_ids = {fact["fact_id"] for fact in scenario["fact_packet"]["facts"]}
        for draft in scenario["drafts"]:
            self.assertTrue(set(draft["fact_ids_used"]) <= packet_ids, draft["platform_id"])

    def test_promotional_tail_fails_with_named_property(self) -> None:
        errors = check(load_fixture("behavioral-promotional-tail.json"))
        self.assertTrue(
            any("property=no-promotional-tail" in error for error in errors), errors
        )

    def test_unknown_fact_asserted_fails_with_named_property(self) -> None:
        errors = check(load_fixture("behavioral-unknown-as-fact.json"))
        self.assertTrue(
            any("property=unknown-stays-unknown" in error for error in errors), errors
        )

    def test_unexecuted_pass_fails_with_named_property(self) -> None:
        errors = check(load_fixture("behavioral-unexecuted-pass.json"))
        self.assertTrue(
            any("property=unexecuted-check-stays-unknown" in error for error in errors),
            errors,
        )

    def test_decision_pass_despite_unknown_fact_fails_with_named_property(self) -> None:
        errors = check(load_fixture("behavioral-evidence-not-preserved.json"))
        self.assertTrue(
            any("property=evidence-status-preserved" in error for error in errors), errors
        )

    def test_missing_expected_draft_fails_routing(self) -> None:
        scenario = load_fixture("behavioral-scenario-sandblasting.json")
        scenario["drafts"] = [
            draft for draft in scenario["drafts"] if draft["platform_id"] != "zhihu"
        ]
        errors = check(scenario)
        self.assertTrue(any("property=routing" in error for error in errors), errors)

    def test_unexpected_platform_draft_fails_routing(self) -> None:
        scenario = load_fixture("behavioral-scenario-sandblasting.json")
        extra = json.loads(json.dumps(scenario["drafts"][0]))
        extra["article_id"] = "behavioral-toutiao-001"
        extra["platform_id"] = "toutiao"
        extra["skill_name"] = "platform-write-toutiao"
        extra["fact_ids_used"] = ["FACT-BEH-001"]
        scenario["drafts"].append(extra)
        errors = check(scenario)
        self.assertTrue(any("property=routing" in error for error in errors), errors)

    def test_draft_using_unknown_fact_id_fails_grounding(self) -> None:
        scenario = load_fixture("behavioral-scenario-sandblasting.json")
        scenario["drafts"][0]["fact_ids_used"] = ["FACT-BEH-001", "FACT-DOES-NOT-EXIST"]
        errors = check(scenario)
        self.assertTrue(
            any("property=fact-ids-grounded" in error for error in errors), errors
        )


if __name__ == "__main__":
    unittest.main()
