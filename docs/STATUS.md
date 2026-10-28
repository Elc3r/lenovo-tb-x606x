# Hardware and security status

Evidence is from one Lenovo TB-X606X LTE, through 2026-10-28. Publication cleanup
was host-only. It has not been independently rebuilt or validated on another unit.

| Area | Result / limit |
| --- | --- |
| Android | LineageOS 19.1, Android 12L/API32 |
| Cold boot | Enforcing, GSM and RIL running; MD1 support 9 |
| Required HAL registration | Keymaster, camera, Bluetooth, Wi-Fi, power and PQ present |
| Basic hardware | Wi-Fi, touch, sound, both cameras, Bluetooth, rotation tested |
| Lifecycle | Sleep/wake, charging and reboot tested |
| Encryption | Android FBE; TWRP decrypts with/without PIN using matched Beanpod |
| Cellular | SIM detection and mobile data confirmed after NA77/GSM repair; calls/SMS/VoLTE/emergency/roaming/BIP unverified |
| Recovery | Actual flash boot and local ZIP installation work |
| Recovery sideload | Known FunctionFS binding hang; use normal ADB push |
| Recovery temporary boot | Host OKAY followed by Android; not validated |
| Security baseline | Old prebuilt 4.9.190+ kernel/vendor; vendor SPL 2022-05-05 |

Enforcing is not a statement that all domains in a userdebug build are enforcing:
standard `su` and `backuptool` exceptions remain. Recovery itself is permissive.
No newer kernel/vendor fixes, remote attestation or certification are claimed.

Remaining AVCs include expected app sandbox restrictions, optional DSU probes,
BIP's denied private DNS read and a legacy GSM request to stop an absent service.
The AP-side no-DNS fallback is understood; BIP-specific modem acceptance remains
unverified even though ordinary mobile data now works.

Headunit Revived was observed reading credential-encrypted SharedPreferences
before user unlock and throwing IllegalStateException. That is an application
direct-boot compatibility issue; no SELinux permission is added to bypass it.

Future work: test real cellular lifecycle, a second device, long-running use,
and reproducible builds from clean clones. A newer Android branch requires
policy/API/build review; do not simply copy the current generated policy.

The first inserted-SIM test exposed write-open denials on NA77_005, followed by
a modem exception and failed GSM symlink cleanup during recovery. The narrow
repair gives those two existing regular records a separate type and permits
GSM symlink lifecycle. The user rebuilt/installed that change, then confirmed
SIM detection and mobile data. The corresponding audit retained Enforcing,
running RIL and all six required HAL; no modem exception appeared in its capture.
This does not establish long-running or complete telephony functionality.
