# Snoopy speaker identification (Raspberry Pi)

Recognizes **who is speaking** on the Pi and tells the browser which name to use
(Toby, Mum, etc.). Voice prints stay on the SD card — nothing is sent to the cloud.

## Install on the Pi

```bash
cd ~/snoopy/pi/speaker-id
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
sudo apt install -y alsa-utils
```

## Enroll each person (once)

```bash
source .venv/bin/activate
python enroll.py --id toby --name Toby
python enroll.py --id mum --name Mum
```

Each enrollment records **three short clips** with `arecord`.

## Test identification

```bash
python identify.py
```

Prints JSON, for example:

```json
{"profileId": "toby", "displayName": "Toby", "confidence": 0.81}
```

## Run the bridge (keeps running at boot)

```bash
python bridge.py
```

Or install systemd:

```bash
sudo cp ~/snoopy/pi/systemd/snoopy-speaker-bridge.service /etc/systemd/system/
sudo systemctl enable snoopy-speaker-bridge
sudo systemctl start snoopy-speaker-bridge
```

Endpoints (localhost only):

| Method | Path | Purpose |
| ------ | ---- | ------- |
| GET | `/v1/catalog` | List enrolled speakers |
| GET | `/v1/active-speaker` | Last identified speaker |
| POST | `/v1/identify-now` | Record 2s and identify |

## Use with Snoopy in Chromium

Open the Pi kiosk URL (not the normal index):

**http://localhost:8000/index-pi.html?pi=1**

When Toby presses **Start voice agent**, Snoopy identifies the voice, then uses
that person's name in all spoken replies.

See also [docs/SPEAKER-PROFILES.md](../../docs/SPEAKER-PROFILES.md).
