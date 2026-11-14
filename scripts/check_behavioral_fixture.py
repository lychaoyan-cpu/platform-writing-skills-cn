#!/usr/bin/env python3
"""Check a behavioral regression fixture for realistic multi-platform writing.

A scenario bundles one synthetic fact packet, one synthetic project profile,
the expected routing decision (which platform skills are selected), and one
draft record per target platform. The checker validates the packet and each
draft with the repository's own validators, then asserts the structural
properties each draft must keep, whatever its wording is:

- routing: drafts cover exactly the expected platforms, no missing or extra.
- fact-ids-grounded: every ``fact_ids_used`` entry exists in the packet.
- unknown-stays-unknown: a fact whose evidence is UNKNOWN is never asserted
  as a hard figure in a draft body (see ``unknown_parameters``).
- no-promotional-tail: no draft body ends in, or contains, a promotional
  call to action.
- evidence-status-preserved: when a used fact is UNKNOWN the draft decision
  stays REVIEW, and every source record keeps one of the evidence statuses
  of the facts the draft actually uses.
- unexecuted-check-stays-unknown: a check recorded as PASS must carry
  evidence; a check that was not executed stays UNKNOWN.

Every failure names the property that broke, so a failing fixture says
which structural property broke instead of only showing a diff.

Uses only the Python standard library and runs without network access.

Usage:
    python scripts/check_behavioral_fixture.py path/to/scenario.json
    python scripts/check_behavioral_fixture.py   # checks the bundled scenario

Exit code is 0 when the scenario passes and 1 otherwise.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIO = ROOT / "tests" / "fixtures" / "behavioral-scenario-sandblasting.json"
DEFAULT_FACT_PACKET_SCHEMA = ROOT / "schemas" / "fact-packet.schema.json"
DEFAULT_OUTPUT_CONTRACT_SCHEMA = ROOT / "schemas" / "output-contract.schema.json"
DEFAULT_PLATFORMS = ROOT / "config" / "platforms.json"

# Promotional closers a draft must never carry. The list is intentionally
# short and structural: it flags the call-to-action tail, not wording.
PROMOTIONAL_TAIL_MARKERS = (
    "关注我",
    "立即购买",
    "点击链接下单",
    "私信领取",
    "限时优惠",
    "马上抢购",
)

IDENTITY_STATUSES = {"VERIFIED", "USER_PROVIDED", "PENDING", "CONFLICT"}


def load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {relative}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FACT_PACKET_VALIDATOR = load_module("fact_packet_validator", "scripts/validate_fact_packet.py")
OUTPUT_CONTRACT_VALIDATOR = load_module(
    "output_contract_validator", "scripts/validate_output_contract.py"
)


def check_scenario_shape(scenario: object, errors: list[str]) -> dict | None:
    if not isinstance(scenario, dict):
        errors.append("scenario root must be a JSON object")
        return None
    for key in ("scenario_id", "fact_packet", "project_profile", "expected_routing", "drafts"):
        if key not in scenario:
            errors.append(f"scenario: missing required key {key!r}")
    if errors:
        return None
    if not isinstance(scenario["expected_routing"], list) or not scenario["expected_routing"]:
        errors.append("scenario.expected_routing must be a non-empty list")
        return None
    if not isinstance(scenario["drafts"], list) or not scenario["drafts"]:
        errors.append("scenario.drafts must be a non-empty list")
        return None
    return scenario


def check_project_profile(profile: object, errors: list[str]) -> None:
    # Structural presence check only: the shared subset validator does not
    # cover the ``description`` annotation used by the profile schema, so
    # the profile is checked by hand here instead of through that validator.
    where = "scenario.project_profile"
    if not isinstance(profile, dict):
        errors.append(f"{where}: must be a JSON object")
        return
    for key in ("schema_version", "organization", "content"):
        if key not in profile:
            errors.append(f"{where}: missing required property {key!r}")
    if profile.get("schema_version") not in (None, "1.0"):
        errors.append(f"{where}.schema_version: must be '1.0'")
    organization = profile.get("organization")
    if isinstance(organization, dict):
        if not isinstance(organization.get("display_name"), str) or not organization["display_name"]:
            errors.append(f"{where}.organization.display_name: must be a non-empty string")
        if organization.get("identity_status") not in IDENTITY_STATUSES:
            errors.append(
                f"{where}.organization.identity_status: must be one of {sorted(IDENTITY_STATUSES)}"
            )
    elif organization is not None:
        errors.append(f"{where}.organization: must be a JSON object")
    content = profile.get("content")
    if isinstance(content, dict):
        if not isinstance(content.get("language"), str) or not content["language"]:
            errors.append(f"{where}.content.language: must be a non-empty string")
        for key in ("target_audiences", "blocked_claims"):
            if not isinstance(content.get(key), list):
                errors.append(f"{where}.content.{key}: must be a list")
    elif content is not None:
        errors.append(f"{where}.content: must be a JSON object")


def check_routing(scenario: dict, drafts: list[dict], platforms: list[dict], errors: list[str]) -> None:
    expected = scenario["expected_routing"]
    by_id = {item.get("id"): item for item in platforms if isinstance(item, dict)}
    expected_ids: list[str] = []
    for index, target in enumerate(expected):
        if not isinstance(target, dict):
            errors.append(f"scenario.expected_routing[{index}]: must be a JSON object")
            continue
        platform_id = target.get("platform_id")
        if not isinstance(platform_id, str) or platform_id not in by_id:
            errors.append(
                f"scenario.expected_routing[{index}]: unknown platform_id {platform_id!r}"
            )
            continue
        expected_ids.append(platform_id)
        expected_skill = by_id[platform_id].get("skill")
        if target.get("skill_name") not in (None, expected_skill):
            errors.append(
                f"scenario.expected_routing[{index}]: skill_name {target.get('skill_name')!r} "
                f"is not the skill registered for platform_id {platform_id!r}"
            )
    draft_ids = [
        draft.get("platform_id") for draft in drafts if isinstance(draft, dict)
    ]
    for platform_id in expected_ids:
        if platform_id not in draft_ids:
            errors.append(f"draft[{platform_id}].property=routing: expected draft is missing")
    for platform_id in draft_ids:
        if isinstance(platform_id, str) and platform_id not in expected_ids:
            errors.append(
                f"draft[{platform_id}].property=routing: draft for a platform "
                "outside the expected routing"
            )
    if len(draft_ids) != len(set(draft_ids)):
        errors.append("property=routing: duplicate draft for the same platform_id")


def check_draft(
    draft: dict,
    packet_facts: dict[str, dict],
    unknown_parameters: list[dict],
    errors: list[str],
) -> None:
    platform_id = draft.get("platform_id")
    where = f"draft[{platform_id}]" if isinstance(platform_id, str) else "draft[?]"
    fact_ids_used = draft.get("fact_ids_used")
    used_facts: list[dict] = []
    if isinstance(fact_ids_used, list):
        for fact_id in fact_ids_used:
            if not isinstance(fact_id, str):
                continue
            fact = packet_facts.get(fact_id)
            if fact is None:
                errors.append(
                    f"{where}.property=fact-ids-grounded: fact_id {fact_id!r} "
                    "is not in the fact packet"
                )
            else:
                used_facts.append(fact)
    body = draft.get("body") if isinstance(draft.get("body"), str) else ""
    used_ids = {fact.get("fact_id") for fact in used_facts}
    for entry in unknown_parameters:
        if not isinstance(entry, dict):
            continue
        if entry.get("fact_id") not in used_ids:
            continue
        for claim in entry.get("forbidden_claims", []):
            if isinstance(claim, str) and claim and claim in body:
                errors.append(
                    f"{where}.property=unknown-stays-unknown: body asserts "
                    f"forbidden claim {claim!r} for fact {entry.get('fact_id')!r}, "
                    "whose evidence is UNKNOWN"
                )
    for marker in PROMOTIONAL_TAIL_MARKERS:
        if marker in body:
            errors.append(
                f"{where}.property=no-promotional-tail: body contains "
                f"promotional marker {marker!r}"
            )
    used_statuses = {fact.get("evidence_status") for fact in used_facts}
    if "UNKNOWN" in used_statuses and draft.get("decision") != "REVIEW":
        errors.append(
            f"{where}.property=evidence-status-preserved: decision is "
            f"{draft.get('decision')!r} while a used fact has evidence_status UNKNOWN; "
            "expected REVIEW"
        )
    source_records = draft.get("source_records")
    if isinstance(source_records, list):
        for index, record in enumerate(source_records):
            if not isinstance(record, dict):
                continue
            status = record.get("evidence_status")
            if isinstance(status, str) and used_statuses and status not in used_statuses:
                errors.append(
                    f"{where}.source_records[{index}].property=evidence-status-preserved: "
                    f"evidence_status {status!r} does not match any used fact "
                    f"(used statuses: {sorted(used_statuses)})"
                )
    checks = draft.get("checks")
    if isinstance(checks, list):
        for index, check in enumerate(checks):
            if not isinstance(check, dict):
                continue
            result = check.get("result")
            evidence = check.get("evidence")
            if result == "PASS" and evidence is None:
                errors.append(
                    f"{where}.checks[{index}].property=unexecuted-check-stays-unknown: "
                    f"check {check.get('scope')!r} is PASS without evidence"
                )
            if result != "UNKNOWN" and result != "PASS" and evidence is None:
                reason = check.get("reason")
                if isinstance(reason, str) and "not executed" in reason.lower():
                    errors.append(
                        f"{where}.checks[{index}].property=unexecuted-check-stays-unknown: "
                        f"check {check.get('scope')!r} was not executed but is {result!r}"
                    )


def check_scenario(
    scenario: object,
    fact_packet_schema: dict,
    output_contract_schema: dict,
    platforms: list[dict],
) -> list[str]:
    errors: list[str] = []
    scenario = check_scenario_shape(scenario, errors)
    if scenario is None:
        return errors
    packet = scenario["fact_packet"]
    packet_errors = FACT_PACKET_VALIDATOR.validate_packet(packet, fact_packet_schema)
    errors.extend(f"fact-packet: {error}" for error in packet_errors)
    check_project_profile(scenario["project_profile"], errors)
    packet_facts: dict[str, dict] = {}
    if isinstance(packet, dict) and isinstance(packet.get("facts"), list):
        for fact in packet["facts"]:
            if isinstance(fact, dict) and isinstance(fact.get("fact_id"), str):
                packet_facts[fact["fact_id"]] = fact
    drafts = scenario["drafts"]
    for index, draft in enumerate(drafts):
        if not isinstance(draft, dict):
            errors.append(f"scenario.drafts[{index}]: must be a JSON object")
            continue
        record_errors = OUTPUT_CONTRACT_VALIDATOR.validate_record(
            draft, output_contract_schema, platforms
        )
        errors.extend(
            f"drafts[{index}] output-contract: {error}" for error in record_errors
        )
    check_routing(scenario, [d for d in drafts if isinstance(d, dict)], platforms, errors)
    unknown_parameters = scenario.get("unknown_parameters", [])
    if not isinstance(unknown_parameters, list):
        errors.append("scenario.unknown_parameters must be a list")
        unknown_parameters = []
    for draft in drafts:
        if isinstance(draft, dict):
            check_draft(draft, packet_facts, unknown_parameters, errors)
    return errors


def main(argv: list[str]) -> int:
    scenario_path = Path(argv[1]) if len(argv) > 1 else DEFAULT_SCENARIO
    try:
        fact_packet_schema = json.loads(DEFAULT_FACT_PACKET_SCHEMA.read_text(encoding="utf-8"))
        output_contract_schema = json.loads(
            DEFAULT_OUTPUT_CONTRACT_SCHEMA.read_text(encoding="utf-8")
        )
        platforms = json.loads(DEFAULT_PLATFORMS.read_text(encoding="utf-8"))["platforms"]
        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, KeyError) as error:
        print(f"FAIL: cannot load input: {error}")
        return 1
    errors = check_scenario(scenario, fact_packet_schema, output_contract_schema, platforms)
    if errors:
        print(f"FAIL: {len(errors)} behavioral-fixture error(s) in {scenario_path}")
        for error in errors:
            print(f"- {error}")
        return 1
    scenario_id = scenario.get("scenario_id", scenario_path.name)
    print(f"PASS: scenario {scenario_id!r} keeps every structural property")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
