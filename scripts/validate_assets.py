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

    for base in [ROOT / "examples", ROOT / "conformance", ROOT / "benchmarks"]:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.yaml")):
            yaml.safe_load(path.read_text(encoding="utf-8"))
            print(f"yaml OK: {path.relative_to(ROOT)}")

    print(f"validated {len(schemas)} JSON schemas")


if __name__ == "__main__":
    main()
