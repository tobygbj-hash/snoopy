# Snoopy on the Pi — keep it simple

Snoopy grew a lot on paper. On the Pi you only need **one service at a time**
until that works. Everything else is optional.

## What Snoopy actually is

| Piece | What it does | Need it on day one? |
| ----- | ------------ | ------------------- |
| **Scheduling** (`pi/scheduling/`) | Reminders and routines; speaks with **espeak-ng** | **Yes** — best first step |
| **Speaker ID** (`pi/speaker-id/`) | Knows Toby vs Mum vs guest | **Yes** if more than one person |
| **Web + Chromium** (`npm run serve`, kiosk) | Voice **web search** in the browser | **No** — skip if you only want reminders |
| **Chrome extension** | Reads Google AI summaries aloud | **No** — skip on managed/school Chrome |
| **Bookmarklet** | Same summaries without extension | **No** — laptop only |
| **Calendar ICS** | Phone calendar on the Pi | **No** — add when reminders work |

**Zane (RC car)** is separate; it can share the Pi later. It does not use Snoopy’s code.

---

## MVP — do this first (about 30 minutes on the Pi)

Hardware: Pi, USB mic, speaker (Bluetooth is fine), Wi‑Fi.

```bash
sudo apt update
sudo apt install -y git espeak-ng alsa-utils python3-venv

git clone https://github.com/tobygbj-hash/snoopy.git ~/snoopy
cd ~/snoopy/pi/scheduling
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

sudo cp ~/snoopy/pi/systemd/snoopy-scheduler.service /etc/systemd/system/
sudo systemctl enable --now snoopy-scheduler
```

Test (no browser):

```bash
source ~/snoopy/pi/scheduling/.venv/bin/activate
python cli.py remind --profile toby --at "$(date -d '+1 min' +%H:%M)" --message "hello Pi"
```

Wait one minute. You should **hear** the reminder.

That is the core product on the Pi: **local timer + speaker**.

---

## Step 2 — who is speaking (optional but recommended)

Only if multiple people use the same Pi:

```bash
cd ~/snoopy/pi/speaker-id
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python enroll.py --id toby --name Toby
```

Then reminders follow the voice:

```bash
cd ~/snoopy/pi/scheduling && source .venv/bin/activate
python cli.py voice "hey snoopy remind me at 5 30 to feed the dog"
```

Enable the speaker bridge if you use voice ID with other tools:

```bash
sudo cp ~/snoopy/pi/systemd/snoopy-speaker-bridge.service /etc/systemd/system/
sudo systemctl enable --now snoopy-speaker-bridge
```

---

## Step 3 — phone calendar (optional)

One secret ICS link **per person**:

```bash
python cli.py calendar --profile toby --ics-url "YOUR_ICS_URL"
```

Skip this until Step 1 works.

---

## Step 4 — voice web search (optional, more moving parts)

Only if you want “Hey Snoopy, search for …” in the room:

- `snoopy-web.service` (tiny web server)
- Chromium kiosk
- Extension or bookmarklet for AI summaries

Full steps: [pi/README.md](README.md) Phases 3–6. **This is the most complex layer.**

---

## How to avoid scope creep

1. Finish **MVP** (scheduler + one test reminder).
2. Add **speaker ID** if needed.
3. Add **calendar** only if reminders are boring without it.
4. Add **browser/kiosk** last — or never, if you only want a talking reminder clock.

## Tests (any computer, no Pi)

```bash
cd snoopy
npm test
```

That runs privacy checks plus 8 scheduling tests without a microphone.

## When something breaks

| Symptom | Check |
| ------- | ----- |
| No sound | `espeak-ng "test"` and `speaker-test -t wav` |
| Scheduler dead | `systemctl status snoopy-scheduler` |
| Wrong person’s list | `python cli.py show --profile toby` |

More detail only if you need it: [scheduling/README.md](scheduling/README.md).
