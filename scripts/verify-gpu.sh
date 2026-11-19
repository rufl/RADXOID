#!/usr/bin/env bash
set -euo pipefail

# Verify Mali-G52 GPU state on a flashed ROCK 3A via adb.
# Usage: ./scripts/verify-gpu.sh [serial]

SERIAL="${1:-}"
if [[ -z "${SERIAL}" ]]; then
  SERIAL=$(adb devices | awk 'NR>1 && $2=="device" {print $1; exit}')
fi
[[ -n "${SERIAL}" ]] || { echo "no device" >&2; exit 1; }

echo "== GPU vendor =="; adb -s "${SERIAL}" shell getprop ro.hardware.vulkan || true
echo "== Mali libs =="; adb -s "${SERIAL}" shell ls /vendor/lib64/hw/vulkan.*.so /vendor/lib64/libEGL_mali.so /vendor/lib64/libGLESv2_mali.so 2>/dev/null || true
echo "== dmesg Mali =="; adb -s "${SERIAL}" shell dmesg 2>/dev/null | grep -i mali | tail -5 || true
echo "== EGL/GLES =="; adb -s "${SERIAL}" shell getprop ro EGL | grep -iE "vulkan|gl" || true