#!/usr/bin/env bash
set -euo pipefail

# Flash a built ROCK 3A Android image on a Linux host.
# Prefers Rockchip upgrade_tool (full update.img); falls back to rkdeveloptool.
# Usage: ./scripts/flash-rock3a.sh [adb-serial]

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
# shellcheck source=../config/rock3a.env
source "${ROOT_DIR}/config/rock3a.env"

: "${SOURCE_DIR:=${ROOT_DIR}/source}"
case "${SOURCE_DIR}" in
  /*) ;;
  *) SOURCE_DIR="${ROOT_DIR}/${SOURCE_DIR}" ;;
esac

ROCKDEV="${SOURCE_DIR}/rockdev/Image-${PRODUCT_NAME}"
UPDATE="${ROCKDEV}/update.img"
LOADER="${ROCKDEV}/MiniLoaderAll.bin"
[[ -f "${UPDATE}" ]] || { echo "missing ${UPDATE}; build first" >&2; exit 1; }

SERIAL="${1:-}"
if [[ -n "${SERIAL}" ]]; then
  ENABLE="adb -s ${SERIAL} enable-verity; adb -s ${SERIAL} reboot bootloader"
else
  ENABLE="adb enable-verity; adb reboot bootloader"
fi

echo "== entering loader mode =="
bash -c "${ENABLE}" || true
sleep 5

if command -v upgrade_tool >/dev/null; then
  upgrade_tool uf "${UPDATE}"
elif command -v rkdeveloptool >/dev/null; then
  rkdeveloptool db "${LOADER}"
  rkdeveloptool ul "${UPDATE}"
else
  echo "need upgrade_tool or rkdeveloptool in PATH" >&2
  exit 1
fi

echo "flash done"