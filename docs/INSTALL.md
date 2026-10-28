# Installation notes

These are explicit user-run examples, not an automatic installer. They target
only an already unlocked TB-X606X with working fastboot/recovery and a matching
backup. Keep the bootloader unlocked. Do not flash preloader or relock it.
Unlocking or changing encryption backends is a separate data-destructive task;
neither is needed for updates from the tested hardware-Keymaster ROM.

## Recovery

```bash
fastboot getvar product
fastboot getvar unlocked
fastboot getvar partition-size:recovery
fastboot flash recovery /path/to/verified/recovery.img
fastboot reboot recovery
```

Expected product: `achilles6_row_data`, unlocked: yes, recovery size: `2000000`
(hex, 32 MiB). `fastboot boot` did not launch recovery on the tested tablet even
when the host reported success. Stock Android may restore stock recovery on boot.
The current LineageOS setup keeps recovery replacement disabled.

## ROM update from matching LineageOS

First run the host OTA verifier. In working TWRP, unlock data with the PIN if
prompted. Do not save a PIN in command history or scripts. Then:

```bash
adb devices
adb push /path/to/verified/lineage.zip /sdcard/lineage.zip
sha256sum /path/to/verified/lineage.zip
adb shell sha256sum /sdcard/lineage.zip
```

Compare both hashes. In TWRP select Install → the ZIP → confirm installation.
Normal ADB works; ADB sideload has a known FunctionFS bind timeout on this port.
After successful installation, reboot System and unlock Android once so that
credential-encrypted storage is available.

Do not format data for ordinary policy/source updates. Moving from stock FDE
or a different Keymaster backend requires a separately planned clean install.
The development booted with AVB verification disabled; no generic vbmeta command
is prescribed here because host fastboot versions handled this device differently.
Never use a blank or unrelated vbmeta image to work around a verifier failure.

For rollback, preserve a known-working Lineage boot image and matching recovery
before any enforcing experiment. A stock Android boot image is not an appropriate
drop-in rollback for an installed LineageOS system.
