# RADXOID GPU driver override

RADXOID uses the POORD2ROID approach as an **app-level** Vulkan override. The stock Rockchip Mali-G52 driver remains the system default.

## Why not replace the system driver?

Android's Vulkan loader resolves the board's vendor HAL from `/vendor/lib[64]/hw/vulkan.*.so`. Replacing it would affect SurfaceFlinger, codecs, and every app, and the MaliSX2 package is intended for cooperating emulator loaders rather than a drop-in Rockchip HAL.

A rootless system-wide override would require a correctly packaged Android Game Driver APK and matching Android 11 framework policy. That is a separate integration and is not enabled by this first overlay.

## Build the overlay

```bash
./scripts/fetch-gpu-driver.sh
./scripts/package-gpu-overlay.sh
```

The result is:

```text
artifacts/radxoid-gpu-overlay-0.5.0.zip
```

It contains:

```text
product/etc/radxoid/gpu-drivers/gpu-overrides.conf
product/etc/radxoid/gpu-drivers/driver-lock.env
product/etc/radxoid/gpu-drivers/malisx2-0.5.0.zip
```

The archive is a product-partition overlay payload, not a complete flash image. It must be included in the Android product build or installed by the RADXOID launcher/system integration.

## App integration

The cooperating emulator/app should import the driver archive into private storage and use the POORD2ROID-style loader contract:

```text
backend=malisx2
library=libvulkan_malisx2.so
require_custom=0
```

Runtime requirements:

- Android API 29+
- ARM64
- `/dev/mali0`
- Arm Mali kernel driver, not Panfrost-only
- driver selected before `vkCreateInstance`
- explicit `system` fallback

Do not set `require_custom=1` in the default profile. A failed custom driver must return to stock Vulkan rather than leave the app without a renderer.

## Validation on ROCK 3A

First benchmark stock Vulkan, then MaliSX2 in a cooperating emulator. Record:

- Vulkan device and driver name
- API/driver version
- 720p/1080p sustained frame time
- GPU frequency and temperature
- shader/pipeline compilation time
- crashes in `logcat`

MaliSX2 0.5.0 lists Mali-G52 support and Arm-kernel-driver requirements, but no ROCK 3A result is implied by that support list.
