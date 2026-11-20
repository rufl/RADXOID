#!/usr/bin/env bash
set -euo pipefail

# Apply the RADXOID desktop/gaming profile to an already flashed device.
# Usage: ./scripts/apply-device-qol.sh [adb-serial]
SERIAL="${1:-}"
ADB=(adb)
if [[ -n "${SERIAL}" ]]; then
  ADB+=( -s "${SERIAL}" )
fi

[[ -n "$(${ADB[@]} get-state 2>/dev/null || true)" ]] || {
  echo "No online ADB device found" >&2
  exit 1
}

put() {
  local namespace="$1" key="$2" value="$3"
  "${ADB[@]}" shell settings put "${namespace}" "${key}" "${value}"
}

# HDMI/keyboard/mouse defaults. All are reversible through Android Settings.
put system screen_off_timeout 2147483647
put system pointer_speed 1
put system accelerometer_rotation 0
put system show_touches 0
put global window_animation_scale 0.5
put global transition_animation_scale 0.5
put global animator_duration_scale 0.5
put global notification_bubbles 0
put secure immersive_mode_confirmations confirmed
put global stay_on_while_plugged_in 3

echo "RADXOID device QOL profile applied to ${SERIAL:-default ADB device}."
