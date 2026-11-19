#!/usr/bin/env bash
set -euo pipefail

# Debloat for ROCK 3A Android 11: remove Google GMS, telephony/TV/print/carrier
# packages and heavy launchers/wallpapers to minimize the system image for
# gaming/emulation. Idempotent: re-running leaves one filter block.

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
# shellcheck source=../config/rock3a.env
source "${ROOT_DIR}/config/rock3a.env"

: "${SOURCE_DIR:=${ROOT_DIR}/source}"
case "${SOURCE_DIR}" in
  /*) ;;
  *) SOURCE_DIR="${ROOT_DIR}/${SOURCE_DIR}" ;;
esac

MK="${SOURCE_DIR}/device/rockchip/rk356x/rk356x_rock_3a_r/rk356x_rock_3a_r.mk"
[[ -f "${MK}" ]] || { echo "device mk not found: ${MK}" >&2; exit 1; }

if grep -q '^# RADXOID_LEAN_DEBLOAT_APPLIED$' "${MK}"; then
  echo "debloat: already applied, skipping"
  exit 0
fi

# Carrier APN/SPN copies are telephony-only; the ROCK 3A has no modem.
sed -i '/apns-full-conf.xml/d; /spn-conf.xml/d' "${MK}"

# filter-out on the accumulated PRODUCT_PACKAGES list runs after all
# inherit-product calls, so it catches packages from any included mk.
cat >> "${MK}" <<'EOF'

# RADXOID_LEAN_DEBLOAT_APPLIED
PRODUCT_PACKAGES := $(filter-out \
    GmsCore \
    GoogleServicesFramework \
    Phonesky \
    GoogleOneTimeInitializer \
    GoogleLoginService \
    GoogleBackupTransport \
    GooglePartnerSetup \
    GoogleCalendarSyncAdapter \
    GoogleContactsSyncAdapter \
    TvSettings \
    TvProvider \
    LiveTvChannel \
    Phone \
    TeleService \
    TelephonyProvider \
    MmsService \
    Email \
    Exchange \
    Launcher3QuickStepGo \
    Books \
    PlayBooks \
    Music \
    PlayMusic \
    Videos \
    PlayMovies \
    News \
    PlayNewsstand \
    Magazines \
    PrintSpooler \
    PrintRecommendationService \
    CarrierConfig \
    CarrierServices \
    LiveWallpapers \
    LiveWallpapersPicker \
    WallpaperPicker \
    Gallery2 \
  , $(PRODUCT_PACKAGES))
EOF

echo "debloat: ${MK} filtered ($(grep -c '^    ' <<< "$(sed -n '/RADXOID_LEAN_DEBLOAT_APPLIED/,$p' "${MK}")") packages)"