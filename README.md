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

The RK3568 contains a Mali-G52 Bifrost GPU. The default image keeps the Rockchip Mali userspace driver shipped with the matching Radxa BSP; Android GPU drivers are kernel/userspace ABI pairs, so substituting an unrelated newer binary can break SurfaceFlinger or games.

Panfrost/Mesa is tracked as an experimental alternative, not enabled by default:

- Mesa documents Mali-G52 OpenGL ES 3.1 and Vulkan 1.3 support.
- The Android kernel/userspace integration, Rockchip display HAL, and Android gralloc path still require board validation.
- The community RK3568 Panfrost work reports DDK mismatch problems with closed Mali blobs and OPP/devfreq problems when Mali and Panfrost are mixed.
- Never install both Mali and Panfrost paths in one image without a matching kernel, HAL, gralloc, and userspace test matrix.

The lean gaming baseline is therefore: native vendor GPU path, no GMS, no desktop bundle, no unnecessary box UI, and a reproducible userdebug build. Emulator APKs and ROMs remain user-installed; no copyrighted game content is included.

## POORD2ROID-style GPU override

The repository now packages a verified optional MaliSX2 0.5.0 archive for cooperating emulator/app loaders:

```bash
./scripts/fetch-gpu-driver.sh
./scripts/package-gpu-overlay.sh
```

The generated product overlay is `artifacts/radxoid-gpu-overlay-0.5.0.zip`. It preserves stock Vulkan as the default and exposes MaliSX2 as an explicit per-app profile. See [`docs/GPU_DRIVER_OVERRIDE.md`](docs/GPU_DRIVER_OVERRIDE.md).

This is not a global driver replacement. Android does not allow an unprivileged overlay to inject a Vulkan driver into arbitrary apps; apps must integrate the POORD2ROID-style loader or use an emulator custom-driver import path.

## Similar projects reviewed

- [Radxa ROCK 3A Android documentation](https://docs.radxa.com/en/rock3/rock3a/other-os/android/low-level-dev) — build target and `build.sh -UACKup` flow.
- [Radxa ROCK 3A image page](https://docs.radxa.com/en/rock3/images) — current official Android image remains Android 11.
- [Radxa Android manifests](https://github.com/radxa/manifests) — pinned source and board files.
- [Radxa ROCK 3A image workflow repository](https://github.com/radxa-build/rock-3a) — official image hosting/build workflow; Android variants are not its current default.
- [redroid](https://github.com/remote-android/redroid-doc) — current Android 16/15/14 container images and GPU mode model; useful for emulator/container research, not a ROCK 3A boot image.
- [redroid Mali-G52 investigation](https://github.com/1yeshen/redroid-mali-g52) — documents RK3568 Mali DDK compatibility and Panfrost bring-up risks.
- [Mesa Panfrost](https://docs.mesa3d.org/drivers/panfrost.html) — open-source Mali-G52 capability reference.

## Endeavour Linux host

Arch is suitable for repository validation, driver packaging, APK/NDK work, and hardware testing. It is not the conservative native host for this legacy Android 11 BSP; use a pinned Ubuntu 20.04 container or VM for the full vendor build.

The current `prepare.sh` bootstraps Google's official `repo` launcher into `.tools/repo` when no system `repo` exists. This removes one Arch package prerequisite, not the source-storage requirement. The Android tree and output need more than 150 GB in practice; do not start a sync on a nearly-full filesystem. See [`docs/ARCH_HOST.md`](docs/ARCH_HOST.md).

## Build

Host requirements: Ubuntu 20.04 x86_64 is the conservative choice. Android source plus build output needs substantial free storage; plan for more than 150 GB and at least 16 GB RAM. Use a fast SSD and enable ccache for repeat builds.

```bash
./scripts/validate.sh
./scripts/prepare.sh
./scripts/build.sh
```

`prepare.sh` downloads the Radxa/Rockchip source with `repo`, verifies the manifest commit, and syncs the pinned projects. `build.sh` selects the board target and invokes the vendor image builder. Output is under `source/IMAGE`.

Optional containerized build environment:

```bash
docker build -t radxoid-builder .
docker run --rm -it \
  -v "$PWD:/work" \
  -v "$HOME/.ccache:/root/.ccache" \
  radxoid-builder

cd /work
./scripts/validate.sh
./scripts/prepare.sh
./scripts/build.sh
```

For repeat builds, set `REPO_JOBS` and `BUILD_JOBS`:

```bash
REPO_JOBS=8 BUILD_JOBS=12 ./scripts/prepare.sh
REPO_JOBS=8 BUILD_JOBS=12 ./scripts/build.sh
```

## Flashing

The exact generated filenames depend on the Radxa packer. Inspect `source/IMAGE` before flashing. Use Radxa's ROCK 3 installation guide and `rkdeveloptool`/SD writer appropriate to the generated image. Verify the target block device before writing; flashing destroys its existing data.

## Limits

- No ROCK 3A Android 12+ board target was found in Radxa's public manifests; Android 11 is the latest board-supported baseline identified here.
- This repository does not claim CTS/GMS certification.
- GPU performance, emulator compatibility, thermals, controller mappings, and Vulkan behavior require hardware testing on the exact ROCK 3A RAM/storage variant.
- Do not redistribute proprietary Rockchip/Mali blobs outside their original license terms.
