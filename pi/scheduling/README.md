# Snoopy scheduling on the Raspberry Pi

Reminders, daily routines, and **per-person calendars** — entirely on the Pi.
**No browser required.** When it is time to speak, the scheduler uses
**espeak-ng** through your speaker (Bluetooth or USB).

Each enrolled voice (Toby, Mum, etc.) gets their **own** reminders, routines,
and optional calendar link. When someone speaks, Snoopy identifies them first,
then saves or lists **only their** schedule.

## Install

```bash
sudo apt install -y espeak-ng alsa-utils
cd ~/snoopy/pi/scheduling
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdir -p ~/.config/snoopy
cp config.example.json ~/.config/snoopy/config.json
```

Enroll voices first (`pi/speaker-id/README.md`), then:

```bash
sudo cp ~/snoopy/pi/systemd/snoopy-scheduler.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now snoopy-scheduler
```

Check:

```bash
curl -s http://127.0.0.1:8766/v1/status
```

## Voice command (identifies speaker from mic)

```bash
cd ~/snoopy/pi/scheduling && source .venv/bin/activate
python cli.py voice "hey snoopy remind me at 5 30 to feed the dog"
python cli.py voice "hey snoopy list my reminders"
python cli.py voice "hey snoopy list my calendar"
```

Snoopy records ~2 seconds, matches the voice print, then attaches the command to
that **profileId**.

## CLI examples

```bash
# Reminder for Toby without re-identifying (profile known)
python cli.py remind --profile toby --at 17:30 --message "homework"

# Routine weekdays 7:15 for Mum
python cli.py routine --profile mum --at 7:15 --message "leave for work" --weekdays

# Mum's Google Calendar secret ICS link
python cli.py calendar --profile mum --ics-url "https://calendar.google.com/calendar/ical/…"

# Show one person
python cli.py show --profile toby

# Everyone
python cli.py show
python cli.py profiles
```

## Per-person phone calendar

1. On the phone, open calendar settings for **that person's** calendar.
2. Copy the **secret ICS / iCal** link (Google: Integrate calendar → secret address).
3. Run `python cli.py calendar --profile <id> --ics-url "…"` for that same profile id
   you used in `enroll.py --id …`.

Toby's calendar is never mixed with Mum's — separate files under
`~/.config/snoopy/`.

## HTTP API (optional automation)

| Method | Path | Notes |
| ------ | ---- | ----- |
| POST | `/v1/voice-command` | Body: `{"transcript":"…"}` — identifies speaker |
| GET | `/v1/schedule?profileId=toby` | One profile |
| GET | `/v1/schedule` | All profiles |
| POST | `/v1/calendar/config` | Body: `profileId`, `icsUrl`, `enabled` |

## Data on the SD card

| File | Contents |
| ---- | -------- |
| `scheduling.json` | Per-profile reminders and routines |
| `config.json` | Per-profile calendar URLs |
| `calendar_caches.json` | Cached ICS events per profile |

## Privacy

- No Snoopy cloud; optional fetch only to **your** ICS URL per person.
- Guest/unrecognized voice uses the `guest` profile unless enrollment improves.

See [docs/SCHEDULING.md](../../docs/SCHEDULING.md).
