from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    import yaml
    from jsonschema import Draft202012Validator

    schemas = {}
    for path in sorted((ROOT / "schemas").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(data)
        schemas[path.name] = data
        print(f"schema OK: {path.relative_to(ROOT)}")

    scenario_schema = schemas.get("scenario.schema.json")
    scenario_validator = Draft202012Validator(scenario_schema) if scenario_schema else None
    yaml_count = 0
    scenario_count = 0
    for base in [ROOT / "examples", ROOT / "conformance", ROOT / "benchmarks"]:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.yaml")):
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
            yaml_count += 1
            print(f"yaml OK: {path.relative_to(ROOT)}")
            if isinstance(document, dict) and document.get("kind") == "ScenarioTemplate":
                errors = sorted(scenario_validator.iter_errors(document), key=lambda error: list(error.absolute_path)) if scenario_validator else []
                if errors:
                    joined = "; ".join(error.message for error in errors)
                    raise SystemExit(f"scenario schema FAIL: {path.relative_to(ROOT)}: {joined}")
                scenario_count += 1
                print(f"scenario OK: {path.relative_to(ROOT)}")

    packaged = ROOT / "src" / "avp_ref" / "resources" / "scenario.schema.json"
    canonical = ROOT / "schemas" / "scenario.schema.json"
    if packaged.exists() and packaged.read_bytes() != canonical.read_bytes():
        raise SystemExit("packaged scenario schema is out of sync with schemas/scenario.schema.json")

    print(f"validated {len(schemas)} JSON schemas, {yaml_count} YAML assets, {scenario_count} ScenarioTemplates")


if __name__ == "__main__":
    main()
