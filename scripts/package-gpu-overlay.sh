#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
"${ROOT_DIR}/scripts/fetch-gpu-driver.sh"
command -v zip >/dev/null || { echo "zip is required" >&2; exit 1; }

# shellcheck source=../config/gpu-drivers.env
source "${ROOT_DIR}/config/gpu-drivers.env"
archive="${ROOT_DIR}/artifacts/drivers/malisx2/malisx2-${MALISX2_VERSION}.zip"
out_dir="${ROOT_DIR}/artifacts/radxoid-gpu-overlay"
out_zip="${ROOT_DIR}/artifacts/radxoid-gpu-overlay-${MALISX2_VERSION}.zip"
rm -rf "${out_dir}" "${out_zip}"
mkdir -p "${out_dir}/product/etc/radxoid/gpu-drivers"
cp "${ROOT_DIR}/overlay/radxoid-gpu/etc/radxoid/gpu-overrides.conf" \
  "${out_dir}/product/etc/radxoid/gpu-drivers/gpu-overrides.conf"
cp "${ROOT_DIR}/overlay/radxoid-gpu/README.md" \
  "${out_dir}/product/etc/radxoid/gpu-drivers/README.md"
cp "${archive}" "${out_dir}/product/etc/radxoid/gpu-drivers/"
cp "${ROOT_DIR}/config/gpu-drivers.env" \
  "${out_dir}/product/etc/radxoid/gpu-drivers/driver-lock.env"

( cd "${out_dir}" && zip -qr "${out_zip}" product )
printf 'created %s\n' "${out_zip}"
