#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="."
MODE="${CHECK_MODE:-warn}"
POSITIONAL_SET=0

usage() {
  cat <<'EOF'
Usage: check_consistency.sh [project_root] [--mode strict|warn]

Environment:
  PYTHON_BIN          Python executable to run prdctl.py (default: python3)
  PRD_ROOT            Override detected PRD root
  CHECK_MODE          Default check mode when --mode is omitted
  HARNESS_SYNC_MODE   auto|code|prd|off
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode=strict)
      MODE="strict"
      shift
      ;;
    --mode=warn)
      MODE="warn"
      shift
      ;;
    --mode)
      if [[ $# -lt 2 ]]; then
        echo "[harness:check-consistency] missing value for --mode" >&2
        exit 2
      fi
      MODE="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    --*)
      echo "[harness:check-consistency] unknown option: $1" >&2
      exit 2
      ;;
    *)
      if [[ "${POSITIONAL_SET}" -eq 1 ]]; then
        echo "[harness:check-consistency] unexpected extra positional argument: $1" >&2
        exit 2
      fi
      PROJECT_ROOT="$1"
      POSITIONAL_SET=1
      shift
      ;;
  esac
done

case "${MODE}" in
  warn|strict)
    ;;
  *)
    echo "[harness:check-consistency] invalid mode=${MODE}" >&2
    exit 2
    ;;
esac

PYTHON_BIN="${PYTHON_BIN:-python3}"
HARNESS_SYNC_MODE="${HARNESS_SYNC_MODE:-auto}"

detect_prd_root() {
  if [[ -d "${PROJECT_ROOT}/docs/produc" ]]; then
    echo "docs/produc"
  elif [[ -d "${PROJECT_ROOT}/docs/prd" ]]; then
    echo "docs/prd"
  elif [[ -d "${PROJECT_ROOT}/docs/product" ]]; then
    echo "docs/product"
  else
    echo "docs/prd"
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
  git -C "${PROJECT_ROOT}" status --porcelain=v1 --untracked-files=all \
    | sed -E 's/^...//' \
    | sed -E 's#.* -> ##'
}

is_code_related_path() {
  local path="$1"

  if [[ -z "${path}" ]]; then
    return 1
  fi

  case "${path}" in
    "${PRD_ROOT}"/*|docs/*|*.md)
      return 1
      ;;
  esac

  if echo "${path}" | grep -Eq '^(src|app|pages|views|router|routes|components|layouts|features|modules|store|stores|service|services|api|mock|mocks|lib|utils|hooks|composables|constants|types|schemas|models)/'; then
    return 0
  fi

  if echo "${path}" | grep -Eq '\.(js|jsx|ts|tsx|vue|svelte|css|scss|sass|less|styl|json)$'; then
    return 0
  fi

  return 1
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

  while IFS= read -r path; do
    if is_code_related_path "${path}"; then
      echo "code"
      return 0
    fi
  done <<< "${changed}"

  if echo "${changed}" | grep -Eq "^${PRD_ROOT}/(pages|changelog|01-|02-|03-|04-|system|system-prd|imports|audit|templates)"; then
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
