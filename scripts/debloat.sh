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
    # Google GMS and services (no Play Store, no GMS) \
    GmsCore \
    GoogleServicesFramework \
    Phonesky \
    GoogleOneTimeInitializer \
    GoogleLoginService \
    GoogleBackupTransport \
    GooglePartnerSetup \
    GoogleCalendarSyncAdapter \
    GoogleContactsSyncAdapter \
    GoogleFeedback \
    GooglePlayServices \
    GoogleServicesFramework \
    \
    # Telephony (ROCK 3A has no modem) \
    Phone \
    TeleService \
    TelephonyProvider \
    MmsService \
    Stk \
    ImsService \
    ImsTelephony \
    \
    # TV and media center \
    TvSettings \
    TvProvider \
    LiveTvChannel \
    TvInputDtv \
    TvInputPassthrough \
    TvRemoteService \
    TvRemoteProvider \
    \
    # Print services \
    PrintSpooler \
    PrintRecommendationService \
    PrintServiceBroker \
    \
    # Carrier services \
    CarrierConfig \
    CarrierServices \
    CarrierDefaultApp \
    \
    # Heavy launchers and wallpapers \
    Launcher3QuickStepGo \
    LiveWallpapers \
    LiveWallpapersPicker \
    WallpaperPicker \
    Gallery2 \
    GalleryNew \
    \
    # Media apps (not needed for gaming) \
    Books \
    PlayBooks \
    Music \
    PlayMusic \
    MusicFX \
    Videos \
    PlayMovies \
    VideoPlayer \
    MovieStudio \
    News \
    PlayNewsstand \
    Magazines \
    \
    # Email and contacts \
    Email \
    Exchange \
    Exchange2 \
    Contacts \
    ContactsProvider \
    \
    # Calendar \
    Calendar \
    CalendarProvider \
    CalendarSyncAdapter \
    \
    # Browser and web (optional for gaming) \
    Browser2 \
    WebViewGoogle \
    \
    # System apps that can be removed for lean image \
    Calculator \
    CalculatorGoogle \
    Clock \
    DeskClock \
    CalendarClock \
    SoundRecorder \
    FMRadio \
    Radio \
    \
    # Development/debug tools (not needed in production) \
    DevelopmentSettings \
    Bugreporter \
    Dumpstate \
    Logcatd \
    \
    # Accessibility (optional, can be added back if needed) \
    Accessibility \
    AccessibilitySettings \
    TalkBack \
    SwitchAccess \
    \
    # Misc system apps \
    BasicDreams \
    CellBroadcastReceiver \
    CellBroadcastService \
    EmergencyInfo \
    FusedLocation \
    GCS \
    GeocoderProvider \
    HtmlViewer \
    KeyChain \
    Keyguard \
    Launcher3 \
    Launcher3QuickStep \
    ManagedProvisioning \
    NetworkStack \
    PacProcessor \
    PermissionController \
    Provision \
    ProxyHandler \
    SDCard \
    SettingsIntelligence \
    Shell \
    StorageManager \
    UserDictionaryProvider \
    , $(PRODUCT_PACKAGES))
EOF

echo "debloat: ${MK} filtered ($(grep -c '^    ' <<< "$(sed -n '/RADXOID_LEAN_DEBLOAT_APPLIED/,$p' "${MK}")") packages)"
