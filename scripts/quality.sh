#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="${PYTHONPATH:-}:src"

echo "== Python compile =="
python -m compileall -q src tests scripts

echo "== Unit tests =="
python -m unittest discover -s tests -v

echo "== AVP conformance =="
python -m avp_ref.cli conformance

echo "== Schema / YAML assets =="
python scripts/validate_assets.py

echo "== Secret hygiene =="
if grep -RInE --exclude-dir=.git --exclude='MANIFEST.json' '(BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9_]{20,})' .; then
  echo "Potential secret detected" >&2
  exit 1
fi

echo "AVP quality gate passed"
