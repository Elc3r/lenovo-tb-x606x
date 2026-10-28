# Build TWRP for TB-X606X

Use a separate Linux x86-64 checkout. The pinned platform derives from the
minimal-manifest-twrp Android 12.1 manifest. All projects have exact revisions.
Keep a clone of this integration repo alongside the checkout as `port`:

```bash
git clone https://github.com/Elc3r/lenovo-tb-x606x.git port
mkdir twrp-build
cd twrp-build
repo init -u https://github.com/Elc3r/lenovo-tb-x606x.git \
  -b main -m manifests/twrp-pinned.xml
repo sync -c -j4
python3 ../port/scripts/prepare.py --root "$PWD" --tree twrp
python3 ../port/scripts/prepare.py --root "$PWD" --tree twrp --apply
bash device/lenovo/X606X/tools/build.sh
```

The manifest includes the prepared recovery tree at device/lenovo/X606X.
An auxiliary pinned LTE device project at port-inputs/lineage-device supplies
prebuilt/Image.gz via copyfile into the gitignored recovery kernel path.
No full adjacent LineageOS checkout is required. The auxiliary source tree is
not selected as a recovery product.

The helper verifies the imported kernel, recognizes an already applied vold
patch, selects twrp_X606X-eng, enforces VINTF and validates the packed image.
It never runs fastboot/ADB. Output: out/target/product/X606X/recovery.img,
at most 32 MiB. LTE kernel SHA256:
`c9b07e553475373f27946b4c6e4cc03d634558cefc6d0900132a46ae1cd8d8dd`.

For a manual checkout using twrp-upstream-pinned.xml, add the recovery device
repository separately. Supply KERNEL_SOURCE=/path/to/Image.gz, or set
LINEAGE_ROOT=/path/to/lineage-build to import the matching kernel from that tree.
An invalid existing kernel fails before any patch is applied; it is not replaced
silently. Never substitute X606F/FA kernels.

Packed checks establish properties/fstab/kernel and ELF dependency names, not
complete runtime symbol/linker correctness. The matching hardware Keymaster
backend in Android is required for tested FBE behavior; stock FDE is unsupported.
The publication-time manifest/kernel preparation changes have host tests but
have not been independently rebuilt from a complete fresh remote sync.
