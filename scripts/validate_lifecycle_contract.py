"""Cross-check AVP lifecycle schema and conformance state-machine vectors."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas/episode-lifecycle.schema.json"
MATRIX_PATH = ROOT / "conformance/lifecycle/transition-matrix.yaml"
NORMAL_PATH = ROOT / "conformance/lifecycle/normal-path.yaml"
ILLEGAL_PATH = ROOT / "conformance/lifecycle/illegal-transition.yaml"
RECORD_PATH = ROOT / "conformance/lifecycle/transition-record.yaml"


def fail(message: str) -> None:
    raise SystemExit(f"lifecycle contract FAIL: {message}")


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        fail(f"cannot parse {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(ROOT)} must contain a mapping")
    return value


def pair(value: Any, context: str) -> tuple[str, str]:
    if not isinstance(value, list) or len(value) != 2 or not all(isinstance(item, str) for item in value):
        fail(f"{context} must be a two-state list")
    return value[0], value[1]


def main() -> None:
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot parse lifecycle schema: {exc}")
    Draft202012Validator.check_schema(schema)

    try:
        schema_states = schema["$defs"]["episodeState"]["enum"]
    except (KeyError, TypeError) as exc:
        fail(f"schema does not expose $defs.episodeState.enum: {exc}")
    if not isinstance(schema_states, list) or len(schema_states) != len(set(schema_states)):
        fail("schema lifecycle state enum must be a unique list")
    schema_state_set = set(schema_states)

    matrix = load_yaml(MATRIX_PATH)
    states = matrix.get("states")
    transitions = matrix.get("allowed_transitions")
    if not isinstance(states, dict) or not isinstance(transitions, dict):
        fail("transition matrix requires states and allowed_transitions mappings")
    required = states.get("required")
    optional = states.get("optional")
    terminal = states.get("terminal")
    if not all(isinstance(value, list) for value in (required, optional, terminal)):
        fail("required, optional and terminal state sets must be lists")
    required_set, optional_set, terminal_set = set(required), set(optional), set(terminal)
    if required_set & optional_set:
        fail("required and optional states must be disjoint")
    if required_set | optional_set != schema_state_set:
        fail("schema state enum and transition-matrix states differ")
    if not terminal_set <= required_set:
        fail("all terminal states must be required Core states")
    if set(transitions) != schema_state_set:
        fail("allowed_transitions must declare every lifecycle state exactly once")

    allowed_pairs: set[tuple[str, str]] = set()
    for source, targets in transitions.items():
        if not isinstance(targets, list) or len(targets) != len(set(targets)):
            fail(f"transition targets for {source} must be a unique list")
        if not set(targets) <= schema_state_set:
            fail(f"transition targets for {source} contain unknown state")
        if source in terminal_set and targets:
            fail(f"terminal state {source} must not have outbound transitions")
        for target in targets:
            allowed_pairs.add((source, target))

    if "PAUSED" not in optional_set:
        fail("PAUSED must remain an optional Core state in v0.1")
    pause_inbound = {source for source, target in allowed_pairs if target == "PAUSED"}
    if pause_inbound != {"RUNNING"}:
        fail(f"PAUSED inbound transitions must be exactly RUNNING, got {sorted(pause_inbound)}")
    expected_pause_outbound = {"RUNNING", "ABORTED", "INVALID", "INFRA_FAILED"}
    if set(transitions["PAUSED"]) != expected_pause_outbound:
        fail("PAUSED outbound transitions differ from Core pause semantics")

    normal = load_yaml(NORMAL_PATH).get("input", {}).get("transitions")
    if not isinstance(normal, list) or not normal:
        fail("normal-path must provide transitions")
    normal_pairs = [pair(item, "normal-path transition") for item in normal]
    if normal_pairs[0][0] != "CREATED" or normal_pairs[-1][1] != "COMPLETED":
        fail("normal path must run from CREATED to COMPLETED")
    for transition in normal_pairs:
        if transition not in allowed_pairs:
            fail(f"normal path contains illegal transition {transition}")

    illegal_cases = load_yaml(ILLEGAL_PATH).get("cases")
    if not isinstance(illegal_cases, list) or not illegal_cases:
        fail("illegal-transition must contain cases")
    for index, case in enumerate(illegal_cases):
        if not isinstance(case, dict):
            fail(f"illegal case {index} must be a mapping")
        transition = pair(case.get("transition"), f"illegal case {index}")
        if transition in allowed_pairs:
            fail(f"illegal vector is actually allowed: {transition}")

    record_case = load_yaml(RECORD_PATH)
    validator = Draft202012Validator(schema)
    valid_example = record_case.get("valid_example")
    if not isinstance(valid_example, dict):
        fail("transition-record valid_example must be a mapping")
    errors = list(validator.iter_errors(valid_example))
    if errors:
        fail(f"valid transition record fails schema: {errors[0].message}")
    invalid_examples = record_case.get("invalid_examples")
    if not isinstance(invalid_examples, list) or not invalid_examples:
        fail("transition-record must define invalid_examples")
    for index, example in enumerate(invalid_examples):
        if not isinstance(example, dict) or validator.is_valid(example):
            fail(f"invalid transition record example {index} was accepted")

    print(
        "lifecycle contract OK: "
        f"{len(schema_state_set)} states, {len(allowed_pairs)} allowed transitions, "
        f"{len(terminal_set)} terminal states"
    )


if __name__ == "__main__":
    main()
