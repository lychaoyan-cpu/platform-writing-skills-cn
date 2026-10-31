#!/usr/bin/env python3
"""Validate an output-contract record against schemas/output-contract.schema.json.

Uses only the Python standard library. Schema checking reuses the subset
validator from scripts/validate_fact_packet.py, so both commands reject
unsupported schema keywords instead of silently ignoring them and reject
unknown keys (``additionalProperties: false``) instead of ignoring them.

On top of the schema checks it enforces the integration rules that a schema
cannot express:

- ``platform_id`` must resolve against ``config/platforms.json``.
- ``skill_name`` must be the skill registered for that platform id.
- ``fact_ids_used`` entries must be unique within a record.

Usage:
    python scripts/validate_output_contract.py path/to/output-contract.json
    python scripts/validate_output_contract.py          # validates the example

Exit code is 0 when the record is valid and 1 otherwise.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "schemas" / "output-contract.schema.json"
DEFAULT_RECORD = ROOT / "examples" / "output-contract.example.json"
DEFAULT_PLATFORMS = ROOT / "config" / "platforms.json"


def load_schema_validator():
    spec = importlib.util.spec_from_file_location(
        "fact_packet_validator", ROOT / "scripts" / "validate_fact_packet.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load scripts/validate_fact_packet.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SCHEMA_VALIDATOR = load_schema_validator()


def check_platform_and_ids(record: dict, platforms: list[dict], errors: list[str]) -> None:
    by_id = {item.get("id"): item for item in platforms if isinstance(item, dict)}
    platform_id = record.get("platform_id")
    if isinstance(platform_id, str):
        entry = by_id.get(platform_id)
        if entry is None:
            errors.append(f"$.platform_id: unknown platform_id {platform_id!r}")
        else:
            skill_name = record.get("skill_name")
            expected_skill = entry.get("skill")
            if isinstance(skill_name, str) and skill_name != expected_skill:
                errors.append(
                    f"$.skill_name: {skill_name!r} is not the skill registered for "
                    f"platform_id {platform_id!r} (expected {expected_skill!r})"
                )
    fact_ids = record.get("fact_ids_used")
    if isinstance(fact_ids, list):
        seen: set[str] = set()
        for index, fact_id in enumerate(fact_ids):
            if isinstance(fact_id, str):
                if fact_id in seen:
                    errors.append(f"$.fact_ids_used[{index}]: duplicate fact_id {fact_id!r}")
                seen.add(fact_id)


def validate_record(record: object, schema: dict, platforms: list[dict]) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return ["record root must be a JSON object"]
    SCHEMA_VALIDATOR.validate_value(record, schema, "$", errors)
    check_platform_and_ids(record, platforms, errors)
    return errors


def main(argv: list[str]) -> int:
    record_path = Path(argv[1]) if len(argv) > 1 else DEFAULT_RECORD
    schema_path = Path(argv[2]) if len(argv) > 2 else DEFAULT_SCHEMA
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        platforms = json.loads(DEFAULT_PLATFORMS.read_text(encoding="utf-8"))["platforms"]
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, KeyError) as error:
        print(f"FAIL: cannot load input: {error}")
        return 1
    errors = validate_record(record, schema, platforms)
    if errors:
        print(f"FAIL: {len(errors)} output-contract error(s) in {record_path}")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PASS: {record_path} conforms to {schema_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
