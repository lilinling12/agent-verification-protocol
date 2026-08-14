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

    template_schema = schemas.get("scenario-template.schema.json")
    if template_schema is None:
        raise SystemExit("scenario-template.schema.json is required")
    scenario_validator = Draft202012Validator(template_schema)

    legacy_schema = schemas.get("scenario.schema.json")
    if legacy_schema is not None and legacy_schema != template_schema:
        raise SystemExit(
            "legacy schemas/scenario.schema.json must remain an exact semantic mirror of scenario-template.schema.json during compatibility period"
        )

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
                errors = sorted(
                    scenario_validator.iter_errors(document),
                    key=lambda error: list(error.absolute_path),
                )
                if errors:
                    joined = "; ".join(error.message for error in errors)
                    raise SystemExit(
                        f"scenario template schema FAIL: {path.relative_to(ROOT)}: {joined}"
                    )
                scenario_count += 1
                print(f"scenario OK: {path.relative_to(ROOT)}")

    resource_root = ROOT / "src" / "avp_ref" / "resources"
    for name in ("scenario-template.schema.json", "scenario-instance.schema.json"):
        packaged = resource_root / name
        canonical = ROOT / "schemas" / name
        if not packaged.exists() or packaged.read_bytes() != canonical.read_bytes():
            raise SystemExit(f"packaged {name} is out of sync with schemas/{name}")

    legacy_packaged = resource_root / "scenario.schema.json"
    legacy_canonical = ROOT / "schemas" / "scenario.schema.json"
    if legacy_packaged.exists() and legacy_packaged.read_bytes() != legacy_canonical.read_bytes():
        raise SystemExit("packaged legacy scenario schema is out of sync")

    print(
        f"validated {len(schemas)} JSON schemas, {yaml_count} YAML assets, "
        f"{scenario_count} ScenarioTemplates"
    )


if __name__ == "__main__":
    main()
