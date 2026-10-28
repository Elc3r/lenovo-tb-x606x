# Build LineageOS 19.1

Use Linux x86-64 and the host dependencies required by the pinned LineageOS
branch. Standalone validators use Python 3.11+, Git, brotli, e2fsprogs/debugfs,
binutils/readelf and the Android tree's host compiler/libraries. These scripts
never install host packages. Four build jobs were used during development.

## Fetch sources

Keep the small integration checkout outside the Android source directory:

```bash
git clone https://github.com/Elc3r/lenovo-tb-x606x.git port
mkdir lineage-build
cd lineage-build
repo init -u https://github.com/Elc3r/lenovo-tb-x606x.git \
  -b main -m manifests/lineage-pinned.xml
repo sync -c -j4
```

The primary manifest selects exact commits of the prepared common/LTE trees.
The vendor dependency stays at `a96914baed2dbf30c61e53efa23b82a3ae8f1b5e`.
An auxiliary TWRP device project at `port-inputs/twrp-device` supplies the already
inherited Beanpod executable via a manifest copyfile into the gitignored common
keymaster input. That auxiliary tree is not the Android build target.
Do not confuse this source helper with a full TWRP platform checkout.

## Prepare platform patches and private inputs

```bash
python3 ../port/scripts/prepare.py --root "$PWD" --tree lineage
python3 ../port/scripts/prepare.py --root "$PWD" --tree lineage --apply
python3 ../port/scripts/prepare_blobs.py --root "$PWD" \
  --vendor-source "$PWD/vendor/lenovo/mt6765-common" \
  --beanpod "$PWD/device/lenovo/mt6765-common/keymaster/android.hardware.keymaster@4.0-service.beanpod" \
  --install
```

Preparation recognizes the committed device revisions as already integrated.
It checks the exact platform bases and patch hashes before applying the pending
Bionic/init/logd/build/FM patches. Vendor preparation verifies the five inputs
before writing. Four metadata-only ELF normalizations are generated from pinned
vendor Git files, preserving all allocated sections. The source vendor worktree
will contain those explicit prepared differences afterward; do not commit them.
The Beanpod target is gitignored, not a new executable committed in the common tree.

For manual source sets, prepare_blobs.py also supports matching local firmware
or a private cache. See PROVENANCE.md and blobs.json. Do not substitute another
Keymaster backend on existing encrypted userdata. An ordinary update requires
no data format. The FM native disable and prebuilt kernel-header workaround are
explicit patches; their limitations are documented in ARCHITECTURE.md.

## Build and verify

```bash
source build/envsetup.sh
lunch lineage_achilles6_row_data-userdebug
m -j4 selinux_policy
m -j4 bacon
python3 ../port/scripts/verify_ota.py --root "$PWD" \
  --ota out/target/product/achilles6_row_data/lineage-19.1-DATE-UNOFFICIAL-achilles6_row_data.zip \
  --report out/portable-ota-check.json
```

Replace DATE with the actual built filename and use a fresh report path each run.
The verifier supports this product's full v4 block OTA, fixed partition bounds
and uncompressed runtime APEX. Temporary extraction needs several GB. It checks
actual boot/vendor/system/runtime data: device assertion, Enforcing flag, selected
migrations, Beanpod, ECM private symbols/init gates, native property lookup,
initial vendor publication and selected MAC/file-label boundaries including the
SIM recovery repair. It is not the historical full mutation suite, and does not
replace neverallow/Treble build tests or hardware observations.

For bounded setter diagnostics, userdebug optionally accepts
`LINEAGE_RIL_PROPERTY_AUDIT=true`; leave it unset for ordinary builds.
Diagnostics do not establish complete coverage. Preserve actual security patch
metadata rather than changing dates to hide warnings.

## Upstream reproduction alternative

Use `manifests/lineage-upstream-pinned.xml` instead of the primary manifest.
Then prepare.py applies both device and platform patches. This alternative does
not fetch the auxiliary Beanpod source automatically: obtain the exact executable
from the matching recovery tree or local firmware and supply it with --beanpod.
Do not use `--platform-only` on the untouched upstream device trees.
