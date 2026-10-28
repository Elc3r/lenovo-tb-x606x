# Kernel provenance and outstanding source work

LineageOS and LTE TWRP now select the same official September 2023 Lenovo
prebuilt. The earlier June 2022 input remains available in Git history.

## Previous prebuilt

- Path: LTE device tree `prebuilt/Image.gz`.
- SHA256: `fb039df774989a7ca083b63ff77ef2b59c8e6f2352166777c5c82c0e8bd29bdc`.
- Banner: Linux 4.9.190+, June 13, 2022.
- Acquisition in this port: inherited unchanged from
  [the upstream initial device commit](https://github.com/lenovo-mt6765/android_device_lenovo_achilles6_row_data/tree/162ed79f078d29880d84491bc7f82f4e765f0f23).
- Its exact original firmware extraction chain has not been verified against a
  matching official 2022 archive. The device-tree fingerprint is not hash proof.

## Official recovery comparison

The maintainer obtained `TB_X606X_S301085_230919_BMP.zip` through Lenovo Software
Fix. Archive SHA256:
`de476c26c3c4f2da47cbe83113286720ae55ad854b9ebf35a1e4cf0ef31b7c87`.
Its boot and recovery kernels match each other:
`c9b07e553475373f27946b4c6e4cc03d634558cefc6d0900132a46ae1cd8d8dd`.
Their banner reports Linux 4.9.190+, September 19, 2023.

Both builds have identical embedded configuration and appended DTB. Their
decompressed images have the same length (27,553,812 bytes), but differ outside
the build banner. This is not merely a gzip or timestamp difference. Positional
binary differences do not establish a count of source changes or security fixes.
The September kernel is now selected for both LineageOS and TWRP. The matching
Wi-Fi module replaces the older input; its source SHA256 is
`858bf02b16a21e3b6fd795c31cbcea28a3863cf5442513ecbd08d2d298399f95`.
The other seven kernel modules match the official package byte-for-byte.

## Validation of the September selection

On October 28, 2026, the local Lineage build passed actual OTA checks for the
kernel, all eight stripped module payloads, Keymaster and existing policy gates.
It was installed and booted; the collected audit reports Enforcing, all six
required HALs registered, RIL running and successful Wi-Fi association. No new
AVC combinations appeared relative to the preceding capture. These observations
do not establish complete hardware functionality or cellular data performance.

The local TWRP build passed packed-image validation (32,018,432 bytes, within
the previously verified 32 MiB recovery partition). The user flashed/booted it;
the recovery log confirms successful PIN/FBE decryption. Image SHA256:
`62597bfb631ef452c736d28bfbb7aad6208676e78c7241552d021203e5063f52`.
These tests used the development checkouts, not a fresh full remote build.
No private device logs or generated ROM/recovery images are included here.

## Corresponding source remains unresolved

[Lenovo DS543634](https://support.lenovo.com/np/en/downloads/DS543634) lists a
2020 source release. The related
[Yahoo-Mike source tree](https://github.com/Yahoo-Mike/android_kernel_lenovo_X606F)
identifies itself as 4.9.117 in its Makefile. That tree has not been established
as corresponding source for either 4.9.190+ binary above.

The next step is to locate or request the corresponding Lenovo source, vendor
patches, configuration and build scripts for the exact firmware/build. A newer
prebuilt or an attribution notice alone does not supply corresponding source.
The kernel is covered by its own GPL obligations, not this project's Apache
license. See the [Linux licensing documentation](https://www.kernel.org/doc/html/latest/process/license-rules.html).

No claim of completed source compliance or source-reproducible kernel builds is
made. Any future kernel replacement requires separate build and hardware testing.
