# Snoopy scheduling on the Raspberry Pi

Local reminders, daily routines, and optional **phone calendar** sync — nothing
leaves the Pi except fetching **your** private calendar link (ICS) if you turn
that on.

## Install

```bash
cd ~/snoopy/pi/scheduling
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdir -p ~/.config/snoopy
cp config.example.json ~/.config/snoopy/config.json
```

Edit `~/.config/snoopy/config.json` if you like. Calendar URL can also be saved
from **index-pi.html** on the Pi.

## Run at boot

```bash
sudo cp ~/snoopy/pi/systemd/snoopy-scheduler.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable snoopy-scheduler
sudo systemctl start snoopy-scheduler
```

Check:

```bash
curl -s http://127.0.0.1:8766/v1/status
```

Open **http://localhost:8000/index-pi.html?pi=1** (with `npm run serve` and the
speaker bridge if you use voice profiles).

## Voice examples

| Say | What happens |
| --- | --- |
| Hey Snoopy, remind me at 5 30 to feed the dog | One-shot or daily reminder |
| Hey Snoopy, every day at 7 brush teeth | Routine step |
| Hey Snoopy, list my reminders | Shows on screen + short reply |
| Hey Snoopy, list my routine | Routine list |
| Hey Snoopy, list my calendar | Upcoming ICS events |

When a reminder or routine is due, Snoopy speaks on the Pi (Chromium must be
open in kiosk mode).

## Phone calendar (ICS)

1. On your phone or laptop, open your calendar app settings.
2. Find **secret address**, **subscribe URL**, or **ICS** for the calendar you
   want (Google Calendar: Settings → your calendar → Integrate calendar →
   **Secret address in iCal format**).
3. On the Pi page, paste that link, check **Sync phone calendar**, and click
   **Save calendar settings**.

The Pi fetches that URL on a timer. Your calendar provider sees a normal
subscribe fetch — no Snoopy cloud.

**Managed school Google accounts** may block API or secret links; use local
reminders/routines on the Pi, or a personal Google calendar.

## Data files

| File | Purpose |
| ---- | ------- |
| `~/.config/snoopy/scheduling.json` | Reminders and routines |
| `~/.config/snoopy/config.json` | Calendar URL and options |
| `~/.config/snoopy/calendar_cache.json` | Last synced events |

## Privacy

- Reminders and routines are **only** on the SD card.
- Calendar sync uses **your** ICS URL; disable it anytime in config.
- No telemetry, no account system in Snoopy.

See also [docs/SCHEDULING.md](../../docs/SCHEDULING.md).
