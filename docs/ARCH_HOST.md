# Endeavour Linux host

Endeavour Linux is suitable for orchestration, image inspection, APK/NDK work, and board testing. It is not the conservative native host for this legacy Radxa Android 11 BSP: the vendor tree expects an older Android build toolchain than the current Arch rolling stack.

## Safe workflow on Arch

Set the SDK tools already installed locally:

```bash
export ANDROID_SDK_ROOT="$HOME/Android/Sdk"
export PATH="$ANDROID_SDK_ROOT/platform-tools:$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:$PATH"
```

Validate the repository without downloading the Android tree:

```bash
./scripts/validate.sh
bash -n scripts/*.sh
```

When storage is available, `prepare.sh` bootstraps the official `repo` launcher into `.tools/repo` if no system `repo` exists. Override it with `REPO_BIN=/path/to/repo` when required:

```bash
REPO_JOBS=4 ./scripts/prepare.sh
```

When the external drive is mounted, `prepare.sh`/`build.sh` place `SOURCE_DIR` and `CCACHE_DIR` under it (default `/run/media/lich/EdgeBKP/radxoid`), keeping the 150 GB+ tree off the internal disk. Verify space with `df -h` before a sync.

## What this host can do now

- Package and verify the optional MaliSX2 overlay:

  ```bash
  ./scripts/fetch-gpu-driver.sh
  ./scripts/package-gpu-overlay.sh
  ```

- Build a cooperating Android APK/NDK loader or emulator integration using the installed SDK/NDK/CMake.
- Inspect and benchmark a prebuilt ROCK 3A image after connecting the board with `adb`.
- Use Docker later for the Ubuntu 20.04 build environment, after starting the daemon and providing a separate large workspace.

## Container build

The vendor tree is legacy (Android 11, expects JDK 8 / Python 3); build inside the pinned image instead of the Arch host. Mount the workspace and the external drive together:

```bash
docker build -t radxoid-builder:u20.04 .
RUN='docker run --rm -v "$PWD":/work -v /run/media/lich/EdgeBKP:/run/media/lich/EdgeBKP'

# Validate path without downloading (manifest init + pin only):
$RUN -e SKIP_SYNC=1 radxoid-builder:u20.04 -lc 'cd /work && ./scripts/prepare.sh'

# Full sync to the external drive:
$RUN -e REPO_JOBS=8 radxoid-builder:u20.04 -lc 'cd /work && ./scripts/prepare.sh'

# Build:
$RUN -e BUILD_JOBS=12 radxoid-builder:u20.04 -lc 'cd /work && ./scripts/build.sh'
```

The container runs as root, so files it writes on the external drive are root-owned. Hand the workspace back to your user so the space can be released without `sudo`:

```bash
./scripts/fix-ownership.sh
```
The current overlay remains opt-in and per-app. It does not replace Vulkan globally or bypass Android app isolation.
