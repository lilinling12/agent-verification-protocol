#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="${PYTHONPATH:-}:src"

python -m compileall -q src tests scripts
python -m unittest discover -s tests -v
python -m avp_ref.cli conformance
python scripts/validate_assets.py
python scripts/validate_governance.py
python scripts/validate_boundaries.py
python scripts/validate_spec_traceability.py
python scripts/validate_tck_registry.py
python scripts/validate_lifecycle_contract.py

if grep -RInE --exclude-dir=.git --exclude='MANIFEST.json' '(BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9_]{20,})' .; then
  echo "Potential secret detected" >&2
  exit 1
fi

echo "AVP quality gate passed"
