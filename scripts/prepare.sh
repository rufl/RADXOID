#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
# shellcheck source=../config/rock3a.env
source "${ROOT_DIR}/config/rock3a.env"

: "${SOURCE_DIR:=${ROOT_DIR}/source}"
case "${SOURCE_DIR}" in
  /*) ;;
  *) SOURCE_DIR="${ROOT_DIR}/${SOURCE_DIR}" ;;
esac

REPO_BIN="${REPO_BIN:-${ROOT_DIR}/.tools/repo}"
if [[ ! -x "${REPO_BIN}" ]]; then
  command -v curl >/dev/null || { echo "curl is required to bootstrap repo" >&2; exit 1; }
  mkdir -p "$(dirname "${REPO_BIN}")"
  curl --fail --location --retry 3 \
    https://storage.googleapis.com/git-repo-downloads/repo \
    --output "${REPO_BIN}"
  chmod 0755 "${REPO_BIN}"
fi
command -v git >/dev/null || { echo "git is required" >&2; exit 1; }

if ! "${REPO_BIN}" version >/dev/null 2>&1; then
  echo "repo bootstrap is not executable: ${REPO_BIN}" >&2
  exit 1
fi

export PATH="$(dirname "${REPO_BIN}"):${PATH}"

mkdir -p "${SOURCE_DIR}"
cd "${SOURCE_DIR}"

if [[ ! -d .repo ]]; then
  "${REPO_BIN}" init \
    -u "${MANIFEST_URL}" \
    -b "${MANIFEST_BRANCH}" \
    -m "${MANIFEST_NAME}" \
    --depth=1
fi

manifest_dir=.repo/manifests
if ! git -C "${manifest_dir}" rev-parse --git-dir >/dev/null 2>&1; then
  echo "repo initialized without a git manifest checkout" >&2
  exit 1
fi

current_revision=$(git -C "${manifest_dir}" rev-parse HEAD)
if [[ "${current_revision}" != "${MANIFEST_REVISION}" ]]; then
  git -C "${manifest_dir}" fetch --depth=1 origin "${MANIFEST_REVISION}"
  git -C "${manifest_dir}" checkout --detach "${MANIFEST_REVISION}"
fi

jobs="${REPO_JOBS:-$(nproc)}"
if [[ "${SKIP_SYNC:-0}" != 1 ]]; then
  "${REPO_BIN}" sync -c -d --no-tags --optimized-fetch -j"${jobs}"
else
  echo "Manifest pinned to ${MANIFEST_REVISION}; skipping sync (SKIP_SYNC=1)."
fi

# Fixup: the rk12 manifest forgot the rock_3a.config kernel-fragment symlink
# that the 3A BoardConfig references (rock_3b/rock3c got theirs).
if [[ -f "${SOURCE_DIR}/kernel/configs/rockchip/rock_3a.config" ]]; then
  mkdir -p "${SOURCE_DIR}/kernel/kernel/configs"
  ln -sfn ../../configs/rockchip/rock_3a.config \
    "${SOURCE_DIR}/kernel/kernel/configs/rock_3a.config"
fi

echo "Prepared ${PRODUCT_NAME} from manifest ${MANIFEST_REVISION}"

