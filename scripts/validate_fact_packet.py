#!/usr/bin/env python3
"""Validate a fact packet against schemas/fact-packet.schema.json.

Uses only the Python standard library. The validator implements the subset of
JSON Schema (draft 2020-12) that the bundled fact-packet schema actually uses:
``type`` (including type lists), ``const``, ``enum``, ``required``,
``properties``, ``additionalProperties: false``, ``items``, ``minLength``, and
``format: date``. Unsupported keywords are reported instead of being silently
ignored, so a future schema change cannot pass by accident.

On top of the schema checks it enforces two editorial integrity rules that a
schema cannot express:

- ``fact_id`` values must be unique within a packet.
- ``source_id`` values must be unique within a single fact.

Usage:
    python scripts/validate_fact_packet.py path/to/fact-packet.json
    python scripts/validate_fact_packet.py            # validates the example

Exit code is 0 when the packet is valid and 1 otherwise.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "schemas" / "fact-packet.schema.json"
DEFAULT_PACKET = ROOT / "examples" / "fact-packet.example.json"

SUPPORTED_KEYWORDS = {
    "$schema",
    "$id",
    "title",
    "type",
    "const",
    "enum",
    "required",
    "properties",
    "additionalProperties",
    "items",
    "minLength",
    "format",
}

TYPE_CHECKS = {
    "object": lambda value: isinstance(value, dict),
    "array": lambda value: isinstance(value, list),
    "string": lambda value: isinstance(value, str),
    "null": lambda value: value is None,
    "boolean": lambda value: isinstance(value, bool),
    "number": lambda value: isinstance(value, (int, float)) and not isinstance(value, bool),
    "integer": lambda value: isinstance(value, int) and not isinstance(value, bool),
}

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def type_name(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, str):
        return "string"
    if isinstance(value, (int, float)):
        return "number"
    return type(value).__name__


def check_date(value: str) -> bool:
    if not DATE_RE.match(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def validate_value(value: object, schema: dict, where: str, errors: list[str]) -> None:
    unsupported = sorted(set(schema) - SUPPORTED_KEYWORDS)
    if unsupported:
        errors.append(f"{where}: unsupported schema keyword(s): {', '.join(unsupported)}")
        return

    if "const" in schema and value != schema["const"]:
        errors.append(f"{where}: must equal {schema['const']!r}, got {value!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{where}: {value!r} is not one of {schema['enum']}")

    if "type" in schema:
        allowed = schema["type"]
        allowed_list = allowed if isinstance(allowed, list) else [allowed]
        if not any(TYPE_CHECKS[name](value) for name in allowed_list):
            errors.append(f"{where}: expected type {'/'.join(allowed_list)}, got {type_name(value)}")
            return

    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{where}: shorter than minLength {schema['minLength']}")
        if schema.get("format") == "date" and not check_date(value):
            errors.append(f"{where}: {value!r} is not a valid YYYY-MM-DD date")

    if isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            validate_value(item, schema["items"], f"{where}[{index}]", errors)

    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{where}: missing required property {key!r}")
        properties = schema.get("properties", {})
        for key, item in value.items():
            if key in properties:
                validate_value(item, properties[key], f"{where}.{key}", errors)
            elif schema.get("additionalProperties") is False:
                errors.append(f"{where}: additional property {key!r} is not allowed")


def check_unique_ids(packet: dict, errors: list[str]) -> None:
    facts = packet.get("facts")
    if not isinstance(facts, list):
        return
    seen_facts: set[str] = set()
    for index, fact in enumerate(facts):
        if not isinstance(fact, dict):
            continue
        fact_id = fact.get("fact_id")
        if isinstance(fact_id, str):
            if fact_id in seen_facts:
                errors.append(f"facts[{index}]: duplicate fact_id {fact_id!r}")
            seen_facts.add(fact_id)
        sources = fact.get("sources")
        if not isinstance(sources, list):
            continue
        seen_sources: set[str] = set()
        for source_index, source in enumerate(sources):
            if not isinstance(source, dict):
                continue
            source_id = source.get("source_id")
            if isinstance(source_id, str):
                if source_id in seen_sources:
                    errors.append(
                        f"facts[{index}].sources[{source_index}]: duplicate source_id {source_id!r}"
                    )
                seen_sources.add(source_id)


def validate_packet(packet: object, schema: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(packet, dict):
        return ["packet root must be a JSON object"]
    validate_value(packet, schema, "$", errors)
    check_unique_ids(packet, errors)
    return errors


def main(argv: list[str]) -> int:
    packet_path = Path(argv[1]) if len(argv) > 1 else DEFAULT_PACKET
    schema_path = Path(argv[2]) if len(argv) > 2 else DEFAULT_SCHEMA
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"FAIL: cannot load input: {error}")
        return 1
    errors = validate_packet(packet, schema)
    if errors:
        print(f"FAIL: {len(errors)} fact-packet error(s) in {packet_path}")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PASS: {packet_path} conforms to {schema_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
