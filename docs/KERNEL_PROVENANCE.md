# Kernel provenance and outstanding source work

The tested LineageOS and LTE TWRP builds use the same inherited prebuilt. No
kernel replacement was made as part of this provenance investigation.

## Used prebuilt

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
The 2023 kernel was inspected, not selected for this port.

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
