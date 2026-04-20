#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${1:-.}"
MODE="${CHECK_MODE:-warn}"
if [[ "${2:-}" == "--mode=strict" ]]; then
  MODE="strict"
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
if [[ -z "${PRD_ROOT:-}" ]]; then
  if [[ -d "${PROJECT_ROOT}/docs/product" ]]; then
    PRD_ROOT="docs/product"
  elif [[ -d "${PROJECT_ROOT}/docs/prd" ]]; then
    PRD_ROOT="docs/prd"
  else
    PRD_ROOT="docs/product"
  fi
fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRDCTL="${SCRIPT_DIR}/prdctl.py"

echo "[check-consistency] project=${PROJECT_ROOT} mode=${MODE} prd_root=${PRD_ROOT}"
"${PYTHON_BIN}" "${PRDCTL}" diff-sync "${PROJECT_ROOT}" --staged --prd-root "${PRD_ROOT}"
"${PYTHON_BIN}" "${PRDCTL}" audit "${PROJECT_ROOT}" --level strict --prd-root "${PRD_ROOT}"

if [[ "${MODE}" == "strict" ]]; then
  "${PYTHON_BIN}" "${PRDCTL}" audit "${PROJECT_ROOT}" --level strict --fail-on-high --prd-root "${PRD_ROOT}"
fi

echo "[check-consistency] done"
