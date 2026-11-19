#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
ADB_BIN="${ADB_BIN:-${ANDROID_SDK_ROOT:-${HOME}/Android/Sdk}/platform-tools/adb}"

if [[ ! -x "${ADB_BIN}" ]]; then
  echo "adb not found: ${ADB_BIN}" >&2
  exit 1
fi

state=$("${ADB_BIN}" get-state 2>/dev/null || true)
if [[ "${state}" != "device" ]]; then
  echo "No online Android device. Connect the ROCK 3A with USB debugging enabled." >&2
  "${ADB_BIN}" devices -l >&2 || true
  exit 2
fi

shell() {
  "${ADB_BIN}" shell "$@"
}

printf '== identity ==\n'
shell getprop | grep -E 'ro\.product\.(device|model|name)|ro\.build\.version\.(release|sdk)|ro\.board\.platform|ro\.hardware$|ro\.hardware\.egl|ro\.hardware\.vulkan' || true

printf '\n== GPU device ==\n'
shell 'ls -l /dev/mali* /dev/panfrost* 2>/dev/null || true'

printf '\n== Vulkan and EGL libraries ==\n'
shell 'for d in /vendor/lib64/hw /vendor/lib/hw /system/lib64/hw /system/lib/hw; do echo "[$d]"; ls -l "$d"/vulkan* "$d"/*egl* 2>/dev/null || true; done'

printf '\n== SurfaceFlinger renderer ==\n'
shell dumpsys SurfaceFlinger | grep -Ei 'GLES|Vulkan|Mali|Panfrost|renderer|driver' || true

printf '\n== thermal zones ==\n'
shell 'for z in /sys/class/thermal/thermal_zone*/temp; do [ -r "$z" ] && printf "%s " "$z" && cat "$z"; done' || true

printf '\nProbe complete.\n'
