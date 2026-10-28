# Lenovo TB-X606X — LineageOS 19.1 and TWRP

Unofficial port for **Lenovo Tab M10 FHD Plus (2nd Gen), TB-X606X LTE**.
Android product: `achilles6_row_data`. LineageOS 19.1 is **Android 12L / API 32**;
Settings may display the major version as Android 12.

## Status

| Area | Tested result |
| --- | --- |
| Android | Cold-boots with SELinux Enforcing; standard userdebug su/backuptool exceptions remain |
| Cellular | SIM detection and mobile data work on the tested tablet |
| Hardware | Wi-Fi, touch, audio, both cameras, Bluetooth and rotation tested |
| Lifecycle | Sleep/wake, charging and reboot tested |
| Encryption | FBE, matching hardware Beanpod Keymaster, TWRP decryption with/without PIN |
| Recovery | Actual flash boot and internal-storage ZIP installation work |
| DiPlay | CarPlay and forced HEVC playback tested with Enforcing |

One device has been tested. Calls, SMS, VoLTE, emergency/ECM behavior, roaming,
BIP and long-term stability are **not verified**. Recovery sideload has a known
FunctionFS hang; use normal ADB push. Recovery itself is permissive. The old
4.9.190+ prebuilt kernel/vendor are not made current by Enforcing: vendor SPL
is `2022-05-05`, platform baseline reports `2025-03-05`. Both builds now select
the official September 2023 Lenovo kernel, with the matching Wi-Fi module in
LineageOS. Android boot/Wi-Fi/Enforcing and recovery PIN/FBE were checked after
the switch; the full earlier hardware matrix was not repeated.

See [full status](docs/STATUS.md), [installation](docs/INSTALL.md) and
[source/binary provenance](docs/PROVENANCE.md). This is not official LineageOS
or TeamWin support. No binary Release is provided by this initial publication.

## Source repositories

| Repository | Android checkout path |
| --- | --- |
| [Common device tree](https://github.com/Elc3r/android_device_lenovo_mt6765-common) | device/lenovo/mt6765-common |
| [LTE device tree](https://github.com/Elc3r/android_device_lenovo_achilles6_row_data) | device/lenovo/achilles6_row_data |
| [TWRP device tree](https://github.com/Elc3r/android_device_lenovo_X606X_twrp) | device/lenovo/X606X in the recovery checkout |
| This repository | Manifests, platform patches, preparation and documentation |

Use Android's `repo` tool, not Git submodules. `repo sync` fetches separate
projects at exact revisions. The primary manifests select the prepared device
commits and copy the pinned Beanpod/kernel inputs from companion projects.
Bionic/init/logd and build compatibility patches are applied afterward.

## Build

Use Linux x86-64 with the pinned branch's host dependencies. Start with the
integration tools and a separate Android checkout:

```bash
git clone https://github.com/Elc3r/lenovo-tb-x606x.git port
mkdir lineage-build
cd lineage-build
repo init -u https://github.com/Elc3r/lenovo-tb-x606x.git \
  -b main -m manifests/lineage-pinned.xml
repo sync -c -j4
```

Then follow [LineageOS preparation/build](docs/BUILD_LINEAGE.md), including
platform patches and pinned vendor normalization before compilation.
For recovery, use [the TWRP manifest and build guide](docs/BUILD_TWRP.md) in
another checkout. No full neighboring LineageOS checkout is needed for TWRP.

The `*-upstream-pinned.xml` manifests plus the complete patch series remain an
alternative for reproducing the changes from upstream bases. Device history
and existing authorship are retained. [Architecture](docs/ARCHITECTURE.md)
explains why device trees alone are insufficient.

## Verification and contributions

[Validation scope](docs/VALIDATION.md) distinguishes host/actual-OTA checks from
hardware results. The cleaned repository set has not yet been independently
rebuilt from a fresh remote sync. Do not interpret successful source checks as
complete telephony or security certification.

Use this repository's Issues for the port. Include model, source/build revision,
steps and a redacted error excerpt. Do not post PINs, IMEI/IMSI/ICCID, account
tokens, raw modem records or unreviewed full audit captures.
Private firmware archives, signing keys, update journals and record backups
are excluded. Source licenses do not relicense inherited binary dependencies;
review [provenance](docs/PROVENANCE.md) before any separate binary distribution.
