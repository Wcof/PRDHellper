#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HELPER_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET_ROOT="$(cd "${HELPER_ROOT}/.." && pwd)"
PRD_ROOT="${PRD_ROOT:-docs/prd}"
INSTALL_DIR="${TARGET_ROOT}/.agents/skills/create-prd"

BLOCK_START="<!-- create-prd:start -->"
BLOCK_END="<!-- create-prd:end -->"

BLOCK_CONTENT="$(cat <<EOF
${BLOCK_START}
## create-prd

当任务涉及 PRD 初始化、页面 PRD、完整 PRD、Axure HTML 导入、页面变更同步 PRD、代码与 PRD 一致性审计时：

1. 优先阅读 \`.agents/skills/create-prd/SKILL.md\`。
2. PRD 输出目录固定写到目标项目根目录下的 \`${PRD_ROOT}\`，不要写到 \`PRDHellper/docs/\` 或 \`.agents/skills/create-prd/\` 内。
3. 当前环境无 Python 时，跳过脚本命令，直接按 Skill 规则维护 \`${PRD_ROOT}\` 下的 PRD 文档并使用 \`[TODO: ...]\` 标注缺口。
4. 如果后续安装了 Python，再执行：\`bash .agents/skills/create-prd/scripts/check_consistency.sh . --mode=strict\`。
5. 如果仓库里还有其他 \`SKILL.md\` 或说明文件，不要把它们当作 create-prd 本体。

${BLOCK_END}
EOF
)"

upsert_block() {
  local file="$1"
  local heading="$2"
  mkdir -p "$(dirname "${file}")"
  if [[ ! -f "${file}" ]]; then
    {
      echo "# ${heading}"
      echo
      echo "${BLOCK_CONTENT}"
      echo
    } > "${file}"
    return
  fi

  if grep -q "${BLOCK_START}" "${file}" && grep -q "${BLOCK_END}" "${file}"; then
    awk -v start="${BLOCK_START}" -v end="${BLOCK_END}" -v block="${BLOCK_CONTENT}" '
      BEGIN { inblock=0; printed=0 }
      $0 == start { inblock=1; if (!printed) { print block; printed=1 } next }
      $0 == end { inblock=0; next }
      inblock == 0 { print }
      END { if (!printed) { print ""; print block } }
    ' "${file}" > "${file}.tmp"
    mv "${file}.tmp" "${file}"
  else
    {
      cat "${file}"
      echo
      echo "${BLOCK_CONTENT}"
      echo
    } > "${file}.tmp"
    mv "${file}.tmp" "${file}"
  fi
}

echo "== create-prd 无 Python 安装模式 =="
echo "helper 根目录: ${HELPER_ROOT}"
echo "目标项目根目录: ${TARGET_ROOT}"

mkdir -p "${TARGET_ROOT}/.agents/skills"
rm -rf "${INSTALL_DIR}"
cp -R "${HELPER_ROOT}" "${INSTALL_DIR}"
rm -rf "${INSTALL_DIR}/.git" "${INSTALL_DIR}/.pytest_cache"
find "${INSTALL_DIR}" -name ".DS_Store" -type f -delete || true

upsert_block "${TARGET_ROOT}/AGENTS.md" "AGENTS"
upsert_block "${TARGET_ROOT}/CLAUDE.md" "CLAUDE"
upsert_block "${TARGET_ROOT}/.agents/AGENTS.md" "AGENTS"
upsert_block "${TARGET_ROOT}/.claude/CLAUDE.md" "CLAUDE"

mkdir -p "${TARGET_ROOT}/${PRD_ROOT}/pages" "${TARGET_ROOT}/${PRD_ROOT}/system" "${TARGET_ROOT}/${PRD_ROOT}/changelog" "${TARGET_ROOT}/${PRD_ROOT}/audit" "${TARGET_ROOT}/${PRD_ROOT}/imports" "${TARGET_ROOT}/${PRD_ROOT}/templates" "${TARGET_ROOT}/${PRD_ROOT}/.index"

echo "已完成无 Python 安装："
echo "- Skill 安装目录：${INSTALL_DIR}"
echo "- 引导文件：${TARGET_ROOT}/AGENTS.md, ${TARGET_ROOT}/CLAUDE.md, ${TARGET_ROOT}/.agents/AGENTS.md, ${TARGET_ROOT}/.claude/CLAUDE.md"
echo "- PRD 目录骨架：${TARGET_ROOT}/${PRD_ROOT}"
