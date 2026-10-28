# Integration changes

The device trees are only part of the port. `patches/series.json` pins each
platform project's upstream base and patch hash.

- **Bionic:** private fixed ECM storage transaction/bootstrap plus bounded
  userdebug property diagnostics. Canonical/alias storage preparation and
  publication preserve the reviewed old-key semantics; this is branch-specific.
- **system/core:** init ECM publisher readiness gate, matching setter dispatch,
  selected boot diagnostics and optional bounded RIL setter metadata sink.
- **system/logging:** bounded read-only `auditctl -s`, preserving existing -r.
- **vendor/lineage:** preserves the development prebuilt-kernel compatibility
  workaround that replaces the unused generated-kernel-includes command with
  a no-op. This is not a kernel-header implementation or a general upstream fix.
  Revisit it when moving to a real kernel-source/header build.
- **FMRadio:** disables the incompatible native `jni/fmr/Android.mk` module by
  renaming it to `.disabled`, as in the working workspace. FM is not a tested
  feature of this port. This is separate from audio/media migrations.
- **TWRP system/vold:** matching upstream device-tree patch removes the Android
  12 Keymaster blob magic wrapper for the stock Beanpod compatibility path.

Device policy covers dedicated MTK services, property contracts, parent path
traversal and narrow observed operations. Camera/graphics configuration stays
private; calibration/EEPROM and user data are not rewritten. Logger/proinfo
retirements are pinned transformations with reviewed unwind metadata, not broad
partition/device grants. Optional keybox boot-status service is disabled without
fabricating success or enabling provisioning. No updater performs TEE commands.

Historical diagnostic tooling and abandoned ECM broker/snapshot candidates are
excluded from the common source export. The active ECM implementation is carried
in the Bionic/init patches; it is not replaced by those rejected alternatives.
