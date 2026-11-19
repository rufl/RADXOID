#!/usr/bin/env bash
# Hand the external workspace back to the host user after container runs
# that created files as root (repo sync / build inside Docker run as uid 0).
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
# shellcheck source=../config/rock3a.env
source "${ROOT_DIR}/config/rock3a.env"

for d in "${SOURCE_DIR}" "${CCACHE_DIR}"; do
  [[ -n "${d}" && -d "${d}" ]] || continue
  owner=$(stat -c '%u:%g' "${d}")
  if [[ "${owner}" == "$(id -u):$(id -g)" ]]; then
    echo "${d}: already owned by current user"
    continue
  fi
  echo "chown -R $(id -u):$(id -g) ${d}  (needs sudo; files are ${owner})"
  sudo chown -R "$(id -u):$(id -g)" "${d}"
done

printf 'ownership normalized.\n'
