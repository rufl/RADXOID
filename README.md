# RADXOID

Lean Android image build for the Radxa ROCK 3A (`RK3568`).

## Decision

The board target is pinned to the newest Radxa-published ROCK 3A Android source that is currently documented and reproducible:

- Android 11, API 30
- Radxa manifest branch `Android11_Radxa_rk12`
- manifest revision `116eac8ed8e7b29ff17d9a71fa8d1adcb442da57` (2024-08-14)
- product `rk356x_rock_3a_r`
- kernel DTS `rk3568-rock-3a`
- Rockchip Android BSP kernel/U-Boot and Mali-G52 userspace from the same source set
- `userdebug`, without the `_box` product or GMS additions

This is intentionally not AOSP `android-latest-release` by itself. AOSP currently publishes newer platform releases, but the Radxa support matrix lists ROCK 3A Android support as Android 11. Mixing a newer AOSP platform with the RK3568 vendor HAL, boot chain, and GPU stack would be an unvalidated port rather than a usable image.

The build is native Android for the board, not `redroid` in a Linux container.

## Graphics and gaming strategy

The RK3568 contains a Mali-G52 Bifrost GPU. The default image keeps the Rockchip Mali userspace driver shipped with the BSP. For gaming/emulation workloads, the lean flavor:

- Removes Google GMS, telephony/TV/print/carrier packages and heavy launchers/wallpapers to minimize the system image.
- Applies performance tuning: SCHEDUTIL CPU governor (lower jitter under sustained load) and ART dexpreopt speed-profile for boot-critical apps (SystemUI, Settings, Launcher3QuickStep).
- Keeps the Rockchip Mali-G52 userspace driver (proprietary) for best compatibility with existing emulators.

## Build

### Prerequisites

- Ubuntu 20.04 host (or Docker container `radxoid-builder:u20.04`)
- 150 GB+ free space (source tree)
- 50 GB+ free space for `out/` (build artifacts)
- Docker recommended for reproducible builds on Arch/other hosts

### First build (full)

```bash
# Prepare source tree (150 GB, one-time)
./scripts/prepare.sh

# Full build (hours on USB HDD)
./scripts/build.sh
```

### Fast iteration loop (no full rebuild every time)

`./scripts/build.sh` runs the Rockchip vendor `build.sh`, which reuses `out/` by default (incremental). For device-tree-only iterations (debloat list, kernel config, `config.cfg`), the build only recompiles changed targets:

```bash
# Incremental build: reuses out/, skips full source re-sync
./scripts/build-incremental.sh

# Lean build: also applies the debloat package filter-out
ROCK3A_ENV=lean ./scripts/build-incremental.sh
```

#### Testing debloat without flashing

The lean flavor removes GMS, telephony/TV/print/carrier packages and heavy launchers via `scripts/debloat.sh`. It edits `rk356x_rock_3a_r.mk` only; no source tree churn beyond the filter-out list. To see which packages the device tree declares before/after:

```bash
grep -E "^ [A-Z]" device/rockchip/rk356x/rk356x_rock_3a_r/rk356x_rock_3a_r.mk | head
```

`build.sh` itself does not flash. Flash the produced `source/IMAGE/.../update.img` onto the board only after verifying it boots (`adb devices` reachable).

#### Rebuild trigger rules

- Change `rk356x_rock_3a_r.mk` / `config.cfg` / `parameter.txt`: incremental build rebuilds affected APKs only, no ninja regen.
- Change `BoardConfig.mk` (e.g. partition sizes): `kati --regen` runs once, then ninja continues normally.
- Change `kernel/configs/rockchip/rock_3a.config`: kernel rebuild is triggered; this is the only rebuild that takes tens of minutes even incremental.

Host note: keep `CCACHE_DIR` on the same fast volume as `out/` (external drive by default), otherwise ccache does not survive between runs.

## Fast iteration loop (no full rebuild every time)

`./scripts/build.sh` runs the Rockchip vendor `build.sh`, which can trigger a `kati --regen` over the entire 150 GB tree on USB HDD - slow. For device-tree-only iterations (debloat list, kernel config, `config.cfg`), use the incremental build which only rebuilds changed targets:

```bash
# First time: full build
./scripts/build.sh

# Later: only rebuilds what changed - no kati regen unless BoardConfig.mk changes
./scripts/build-incremental.sh

# Lean build: also applies the debloat package filter-out
ROCK3A_ENV=lean ./scripts/build-incremental.sh
```

### Testing debloat without flashing

The lean flavor removes GMS, telephony/TV/print/carrier and heavy launchers via `scripts/debloat.sh`. It edits `rk356x_rock_3a_r.mk` only; no source tree churn beyond the filter-out list. To see which packages the device tree declares before/after:

```bash
grep -E "^ [A-Z]" device/rockchip/rk356x/rk356x_rock_3a_r/rk356x_rock_3a_r.mk | head
```

`build.sh` itself does not flash. Flash the produced `source/IMAGE/.../update.img` onto the board only after verifying it boots (`adb devices` reachable).

### Rebuild trigger rules

- Change `rk356x_rock_3a_r.mk` / `config.cfg` / `parameter.txt`: incremental build rebuilds affected APKs only, no ninja regen.
- Change `BoardConfig.mk` (e.g. partition sizes): `kati --regen` runs once, then ninja continues normally.
- Change `kernel/configs/rockchip/rock_3a.config`: kernel rebuild is triggered; this is the only rebuild that takes tens of minutes even incremental.

Host note: keep `CCACHE_DIR` on the same fast volume as `out/` (external drive by default), otherwise ccache does not survive between runs.

## Flashing

The exact generated filenames depend on the Radxa packer. Inspect `source/IMAGE` before flashing. Use Radxa's ROCK 3 installation guide and `rkdeveloptool`/SD writer appropriate to the generated image. Verify the target block device before writing; flashing destroys its existing data.

Use the helper:
```bash
./scripts/flash-rock3a.sh [adb-serial]
```

## Verification

After flashing, verify Mali-G52 GPU on the device:
```bash
./scripts/verify-gpu.sh [adb-serial]
```

## Limits

- No ROCK 3A Android 12+ board target was found in Radxa's public manifests; Android 11 is the latest board-supported baseline identified here.
- This repository does not claim CTS/GMS certification.
- GPU performance, emulator compatibility, thermals, controller mappings, and Vulkan behavior require hardware testing on the exact ROCK 3A RAM/storage variant.
- Do not redistribute proprietary Rockchip/Mali blobs outside their original license terms.

## Results

### Latest build (lean flavor)

- **Date**: 2026-11-19 12:34-12:51
- **Manifest**: Android 11, `Android11_Radxa_rk12`, revision `116eac8ed8e7b29ff17d9a71fa8d1adcb442da57`
- **Product**: `rk356x_rock_3a_r-userdebug`
- **Artifacts**:
  - `update.img`: 1.8 GB (sha256: `eb5a202662b8af89fda31e7c8b4dd9375156c74f5445c1150d5bfa41157441d5`)
  - `super.img`: 1.6 GB
  - `rkupdate.img`: 1.7 GB
  - `gpt.img`: 4.1 GB
  - `recovery.img`: 110 MB
  - `boot.img`: 35 MB
  - `dtbo.img`: 607 B
- **Performance**: SCHEDUTIL governor, dexpreopt speed-profile (SystemUI/Settings/Launcher3QuickStep)
- **Debloat**: GMS, telephony, TV, print, carrier, wallpapers removed

### Repository

- **Local**: `/home/lich/lichforge/code/monorepo/RADXOID` (git)
- **Remote**: https://github.com/rufl/RADXOID
- **Commits**:
  - `5407b14`: build-incremental: keep set +u through lunch, use m or make
  - `5216600`: Add SCHEDUTIL governor and dexpreopt fixups to incremental build
  - `44ec0be`: Update files
  - `6d533d8`: feat: add incremental build loop and lean debloat workflow
  - `58d9bf4`: feat(rock3a): Android 11 lean + debloat + performance fixups
