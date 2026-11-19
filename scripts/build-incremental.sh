#!/usr/bin/env bash
set -euo pipefail

# Incremental build for ROCK 3A — reuses out/ (no source re-sync, no clobber),
# so only modules affected by the last device.mk/env change are recompiled.
# Delegates to scripts/build.sh, which applies the same idempotent fixups
# (LOCAL_TIDY, SCHEDUTIL governor, dexpreopt speed-profile, recovery size,
# lean debloat) and then invokes the Rockchip vendor ./build.sh -UACKup to
# produce update.img / super.img under rockdev/Image-* and IMAGE/.
#
# Usage: ./scripts/build-incremental.sh [extra args forwarded to build.sh]

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

echo "==> Build incremental (reuses out/): invoking scripts/build.sh"
exec "${ROOT_DIR}/scripts/build.sh" "$@"
