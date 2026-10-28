# Publication preparation validation

Host-only checks, 2026-10-28. No ROM build, ADB, fastboot, flash, network publish,
account change or device access was performed during this preparation.

## Checks performed

- All eight patches apply to their declared base using isolated Git indexes.
  Patched file bytes were compared against the intended source snapshots.
- Nine portable host tests pass with the local built-tree inputs: boot-flag
  rejection, property parser, CIL attribute access, patch identities, manifest
  renderer overwrite refusal, four ELF metadata normalizations, twelve selected
  migrations/unknown-input rejection, blob-install preflight/exact outputs, and
  regular-file-only SIM label rejection.
- The portable full-OTA verifier passed against the last installed package.
  It checked actual vendor/system/runtime payloads, Enforcing boot, selected
  migrated libraries/daemons, Beanpod, ECM private symbols/init gates, native
  property trie/default publication and selected compiled MAC boundaries.
- The existing 32,018,432-byte recovery passed packed-image validation against
  the cleaned source tree with the exact imported LTE kernel. SHA256:
  `d4fca8893f6acc07b54b0ec2fb2c12ad49ced77b370d9385057af159afa511aa`.
- Source files passed Python parsing, shell syntax, JSON and XML parsing.
  Targeted scans found no known private device identifiers, home paths or
  private-key material in the prepared text files.
- Original workspace source-plan validation still passes. Prepared clones have
  independent Git stores and preserved upstream history. They initially had no
  remotes; approved publication adds only the corresponding Elc3r remotes.

Re-run portable tests:

```bash
python3 scripts/test_host.py
# Optional full local fixture checks, from a machine with a built Android tree:
python3 scripts/test_host.py --root /path/to/lineage-build
```

Without --root, four tests requiring vendor/built inputs are explicitly skipped.
The actual full-OTA CLI is documented in BUILD_LINEAGE.md. Host evidence does not
establish a fresh build, runtime cellular correctness, complete absence of AVCs
or new security fixes. The historical private suite (now 271 checks) was not replaced
with a claim of equivalent portable coverage.

Private raw evidence stays outside the four source repositories. Only this
sanitized account of checks is included here.

## SIM follow-up

The user rebuilt/installed the narrow NA77/GSM repair and confirmed SIM
detection and mobile data. The corresponding actual-OTA verification and audit
passed; Enforcing/RIL/HAL registration stayed valid and no modem exception was
observed in the capture. Those four source-file changes are now also included
in the prepared common tree and its integration patch.
The portable verifier additionally checks their compiled permissions and exact
regular-file labels and passed against that new OTA. It does not claim calls,
SMS, emergency/ECM, roaming or BIP validation.

## Publication manifests and bootstrap

The primary manifests pin the committed Elc3r device trees. The Lineage manifest
copies the inherited matching Beanpod input from an auxiliary recovery project;
the TWRP manifest copies the LTE kernel from an auxiliary LTE device project.
Both copyfile payload identities were checked against their committed objects.
The upstream-only manifests and full patch series remain available separately.

Both primary manifests passed real `repo init`/manifest loading in isolated local
checkouts. The preparation tool recognizes exact integrated device commits;
it still checks platform patch bases. Four isolated kernel-helper tests pass,
covering a ready kernel without a Lineage checkout, explicit kernel import and
early rejection of wrong local/source bytes. Git patch operations in those four
tests are mocked. These bootstrap tests do not constitute a full platform sync,
Android build or new hardware test.

After the approved publication, both primary manifests also passed initialization
directly from GitHub. Selected source projects were actually synced: the two
Lineage device trees plus the auxiliary recovery input, and the TWRP device tree
plus the auxiliary LTE input. The manifest-copied Beanpod/kernel hashes matched
their pins and those project worktrees remained clean. The rest of each Android
platform was not downloaded or built for this check.
