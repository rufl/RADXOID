# RADXOID GPU overlay

This overlay exposes optional per-app Vulkan driver packages to a RADXOID launcher or emulator. It intentionally does **not** replace `/vendor/lib64/hw/vulkan.*.so` and does not alter SurfaceFlinger.

## Included profile

- `system`: stock Rockchip Mali-G52 Vulkan driver; recovery/default path.
- `malisx2`: MaliSX2 0.5.0, for Mali-G52-class hardware using `/dev/mali0`, Android API 29+.

The driver archive is fetched and hash-verified by `scripts/fetch-gpu-driver.sh`; it is not committed to this repository.

## Runtime contract

An app integrating the POORD2ROID-style loader must:

1. Copy the selected archive into app-internal storage.
2. Extract it into an app-private directory.
3. Set `DM_VK_DRIVER_CONFIG` to a generated config containing `backend`, `directory`, and `library`.
4. Set `DM_ANDROID_LIBDIR` to the app's `nativeLibraryDir` containing the loader hooks.
5. Probe Vulkan before starting the workload.
6. Keep `system` as an explicit recovery profile.

The loader must select the driver before creating a Vulkan instance. Live driver switching is unsupported.

## Why this is per-app

Android's Vulkan loader supports one system HAL path and its security model does not allow an unprivileged app to inject arbitrary code into another app. A system-wide override would require a matching Game Driver APK, framework integration, and driver ABI validation. This overlay therefore packages the driver for cooperating emulators/apps rather than silently modifying unrelated apps.
