#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
# shellcheck source=../config/gpu-drivers.env
source "${ROOT_DIR}/config/gpu-drivers.env"

command -v curl >/dev/null || { echo "curl is required" >&2; exit 1; }
command -v sha256sum >/dev/null || { echo "sha256sum is required" >&2; exit 1; }
command -v unzip >/dev/null || { echo "unzip is required" >&2; exit 1; }

artifact_dir="${ROOT_DIR}/artifacts/drivers/malisx2"
archive="${artifact_dir}/malisx2-${MALISX2_VERSION}.zip"
extract_dir="${artifact_dir}/extract"
mkdir -p "${artifact_dir}"

if [[ ! -f "${archive}" ]]; then
  curl --fail --location --retry 3 --output "${archive}.partial" "${MALISX2_URL}"
  mv "${archive}.partial" "${archive}"
fi
printf '%s  %s\n' "${MALISX2_ARCHIVE_SHA256}" "${archive}" | sha256sum --check --status

rm -rf "${extract_dir}"
mkdir -p "${extract_dir}"
unzip -q "${archive}" -d "${extract_dir}"
library_path=$(find "${extract_dir}" -type f -name "${MALISX2_LIBRARY}" -print -quit)
[[ -n "${library_path}" ]] || { echo "${MALISX2_LIBRARY} missing from archive" >&2; exit 1; }
printf '%s  %s\n' "${MALISX2_LIBRARY_SHA256}" "${library_path}" | sha256sum --check --status

printf 'verified %s: archive=%s library=%s\n' \
  "${MALISX2_BACKEND}" "${archive}" "${library_path}"
