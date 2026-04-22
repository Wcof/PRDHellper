#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${1:-.}"
MODE="${CHECK_MODE:-warn}"
if [[ "${2:-}" == "--mode=strict" ]]; then
  MODE="strict"
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
HARNESS_SYNC_MODE="${HARNESS_SYNC_MODE:-auto}"

detect_prd_root() {
  if [[ -d "${PROJECT_ROOT}/docs/produc" ]]; then
    echo "docs/produc"
  elif [[ -d "${PROJECT_ROOT}/docs/product" ]]; then
    echo "docs/product"
  elif [[ -d "${PROJECT_ROOT}/docs/prd" ]]; then
    echo "docs/prd"
  else
    echo "docs/product"
  fi
}

if [[ -z "${PRD_ROOT:-}" ]]; then
  PRD_ROOT="$(detect_prd_root)"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRDCTL="${SCRIPT_DIR}/../prdctl.py"

collect_changed_files() {
  if ! git -C "${PROJECT_ROOT}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    return 0
  fi
  git -C "${PROJECT_ROOT}" status --porcelain | awk '{print $2}'
}

infer_sync_mode() {
  case "${HARNESS_SYNC_MODE}" in
    code|prd|off)
      echo "${HARNESS_SYNC_MODE}"
      return 0
      ;;
    auto)
      ;;
    *)
      echo "invalid"
      return 0
      ;;
  esac

  local changed
  changed="$(collect_changed_files)"

  if [[ -z "${changed}" ]]; then
    echo "off"
    return 0
  fi

  if echo "${changed}" | grep -Eq "^(src/|app/|pages/|router/|routes/)"; then
    echo "code"
    return 0
  fi

  if echo "${changed}" | grep -Eq "^${PRD_ROOT}/(pages|changelog|01-|02-|03-|04-|system-prd|imports|audit|templates)"; then
    echo "prd"
    return 0
  fi

  echo "off"
}

run_sync() {
  local sync_mode="$1"
  case "${sync_mode}" in
    code)
      echo "[harness:check-consistency] sync_mode=code"
      "${PYTHON_BIN}" "${PRDCTL}" sync "${PROJECT_ROOT}" --from-code --prd-root "${PRD_ROOT}"
      ;;
    prd)
      echo "[harness:check-consistency] sync_mode=prd"
      "${PYTHON_BIN}" "${PRDCTL}" sync "${PROJECT_ROOT}" --from-prd --prd-root "${PRD_ROOT}"
      ;;
    off)
      echo "[harness:check-consistency] sync_mode=off"
      ;;
    invalid)
      echo "[harness:check-consistency] invalid HARNESS_SYNC_MODE=${HARNESS_SYNC_MODE}" >&2
      exit 2
      ;;
  esac
}

SYNC_MODE="$(infer_sync_mode)"

echo "[harness:check-consistency] project=${PROJECT_ROOT} mode=${MODE} prd_root=${PRD_ROOT}"
run_sync "${SYNC_MODE}"
"${PYTHON_BIN}" "${PRDCTL}" diff-sync "${PROJECT_ROOT}" --staged --prd-root "${PRD_ROOT}"
"${PYTHON_BIN}" "${PRDCTL}" audit "${PROJECT_ROOT}" --level strict --prd-root "${PRD_ROOT}"

if [[ "${MODE}" == "strict" ]]; then
  "${PYTHON_BIN}" "${PRDCTL}" audit "${PROJECT_ROOT}" --level strict --fail-on-high --prd-root "${PRD_ROOT}"
fi

echo "[harness:check-consistency] done"
