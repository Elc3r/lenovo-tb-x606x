# Source and binary provenance

## Source bases

| Component | Upstream | Base |
| --- | --- | --- |
| Common device | lenovo-mt6765/android_device_lenovo_mt6765-common | 1f36ce47ffbfb55838b282f46ce0c46e6f1b0a28 |
| LTE device | lenovo-mt6765/android_device_lenovo_achilles6_row_data | 162ed79f078d29880d84491bc7f82f4e765f0f23 |
| Vendor dependency | lenovo-mt6765/proprietary_vendor_lenovo_mt6765-common | a96914baed2dbf30c61e53efa23b82a3ae8f1b5e |
| Recovery device | Yahoo-Mike/recovery_device_lenovo_X606FA, android-12.1-fbe | 9a49e442790139f6aa9b1f58f4fcb727718364a0 |
| Lineage manifest | LineageOS/android, lineage-19.1 | dd9a9d84ce7005ff60e5c9f776368c2f3e2fd9ca |
| TWRP manifest | minimal-manifest-twrp/platform_manifest_twrp_aosp, twrp-12.1 | 6dc117d9cbd08430daa16db2013560e1c4017fa8 |

The GitHub names above identify upstreams, not newly published maintainer forks.
Full manifests and patches/series.json pin all other inputs. Device clones retain
upstream history; individual source copyrights and licenses remain in force.
New integration scripts marked Apache-2.0 use the included LICENSE. That license
does not relicense patches, inherited source, kernel images or vendor binaries.

## Added Beanpod service

Source firmware: `TB_X606X_S301085_230919_BMP.zip`, SHA256
`de476c26c3c4f2da47cbe83113286720ae55ad854b9ebf35a1e4cf0ef31b7c87`.
Path: `vendor/bin/hw/android.hardware.keymaster@4.0-service.beanpod`, SHA256
`ac5bf57b05d791d900589d3786289077ac9ed666eae4af9f6101c734242a38a0`.
The tested recovery tree contains an identical executable. The new common-tree
copy is excluded from Git; obtain the matching input locally. No firmware archive
or newly added proprietary executable is bundled in the public source snapshot.

## Four vendor source normalizations

The development workspace's bp_kmsetkey_ca, kmsetkey.default.so,
kmsetkey.mt6765.so and libTEECommon.so differ from the pinned vendor Git base in
non-allocated ELF metadata/padding. All file-backed allocated sections match;
prior full-file equality claims would be incorrect. The exact historical tool
that caused this drift is not established.

`blob-normalization.json` records a small hash-pinned byte recipe from each
upstream file to the tested source identity. It contains padding/header changes,
not embedded complete binaries. prepare_blobs.py checks the original hash,
every preimage, all allocated sections and final hash before installation.
It neither executes the helper nor accesses TEE/RPMB. No behavior modification
is inferred from these metadata-only normalizations.

To avoid needing copies of those four files from firmware, use the pinned vendor
checkout plus the separately extracted Beanpod executable:

```bash
python3 scripts/prepare_blobs.py --root /path/to/lineage-build \
  --vendor-source /path/to/lineage-build/vendor/lenovo/mt6765-common \
  --beanpod /path/to/android.hardware.keymaster@4.0-service.beanpod --install
```

## Kernels and inherited blobs

The Lineage device tree inherits a prebuilt kernel, DTB/DTBO and modules. TWRP
imports the exact LTE kernel locally. Matching LTE Image.gz SHA256:
`fb039df774989a7ca083b63ff77ef2b59c8e6f2352166777c5c82c0e8bd29bdc`.
The recovered kernel identifies as 4.9.190+, built June 2022. A matching complete
kernel-source release/build recipe has not been established in this preparation.
Inherited recovery vendor libraries and X606F/FA prebuilts remain in upstream
history. They are not relicensed by these repositories.

Publishing these source adaptations and redistributing compiled images are
different deliverables. This preparation supplies neither vendor redistribution
permission nor complete corresponding kernel source. Before a binary release,
resolve those inputs and retain the relevant notices/source obligations.

## Excluded material

No device serials, user PINs, account tokens, signing keys, firmware ZIPs, private
audit captures, crash dumps or installation journals are intentionally included.
Inherited public Android test-key references are retained and are not private
release keys. Generated ROM/recovery images belong in a separately reviewed
release process, never in these source repositories.
