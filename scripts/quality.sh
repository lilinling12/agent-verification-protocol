#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="${PYTHONPATH:-}:src"

echo "== Python compile =="
python -m compileall -q src tests scripts

echo "== Dependency policy =="
python scripts/validate_dependencies.py

echo "== Release metadata =="
python scripts/validate_release_metadata.py

echo "== Historical design baseline integrity =="
python scripts/validate_design_baseline.py

echo "== Historical design disposition closure =="
python scripts/validate_historical_disposition.py

echo "== Normative surface closure audit =="
python scripts/validate_normative_surface.py

echo "== Unit tests =="
python -m unittest discover -s tests -v

echo "== Reference implementation smoke suite =="
python -m avp_ref.cli conformance

echo "== Schema / YAML assets =="
python scripts/validate_assets.py

echo "== Repository governance =="
python scripts/validate_governance.py

echo "== Repository boundaries =="
python scripts/validate_boundaries.py

echo "== Spec traceability =="
python scripts/validate_spec_traceability.py

echo "== TCK registry =="
python scripts/validate_tck_registry.py

echo "== Lifecycle contract =="
python scripts/validate_lifecycle_contract.py

echo "== TCK report pipeline =="
python scripts/validate_tck_report.py

echo "== Secret hygiene =="
if grep -RInE --exclude-dir=.git --exclude='MANIFEST.json' '(BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9_]{20,})' .; then
  echo "Potential secret detected" >&2
  exit 1
fi

echo "AVP quality gate passed"
