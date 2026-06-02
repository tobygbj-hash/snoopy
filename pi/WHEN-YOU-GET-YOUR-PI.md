# When your Raspberry Pi arrives

Everything below is already in the repo. You do **not** need a laptop in the room after setup.

## Before the Pi ships to you (any computer)

1. Merge open pull requests for Snoopy on GitHub (especially scheduling).
2. Clone: `git clone https://github.com/tobygbj-hash/snoopy.git`

## On the Pi — first hour

| Order | What | Doc |
| ----- | ---- | --- |
| 1 | Flash Raspberry Pi OS, Wi‑Fi, SSH | [pi/README.md](README.md) Phase 1 |
| 2 | `git clone` and `npm test` in `~/snoopy` | [docs/OPERATIONS.md](../docs/OPERATIONS.md) |
| 3 | Web server at boot (optional, for voice search) | `pi/README.md` Phase 3 |
| 4 | **Scheduling** (reminders, routines, calendars) | [pi/scheduling/README.md](scheduling/README.md) |
| 5 | Enroll each voice (`toby`, `mum`, …) | [pi/speaker-id/README.md](speaker-id/README.md) |
| 6 | Bluetooth speaker + USB mic | `pi/README.md` |

## Quick test (no browser)

```bash
sudo apt install -y espeak-ng
cd ~/snoopy/pi/scheduling && source .venv/bin/activate
python cli.py remind --profile toby --at "$(date +%H:%M)" --message "Pi is ready"
# Wait one minute — you should hear the reminder
```

## Zane RC car on the same Pi

Scheduling does not use GPIO. Zane and Snoopy can share one Pi if RAM is enough (Pi 4 with 2 GB+ recommended).

## Help

- [docs/SCHEDULING.md](../docs/SCHEDULING.md)
- [docs/START.md](../docs/START.md) if a page will not load
