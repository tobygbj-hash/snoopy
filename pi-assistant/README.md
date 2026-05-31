# Snoopy Raspberry Pi Assistant

This is the always-on version of Snoopy for a Raspberry Pi. It listens locally
for Toby's wake phrase, sends the exact spoken search words to Google, tries to
read Google's AI Overview, and speaks the short summary through the Pi speaker.

## What it can and cannot do

- It can run all day on a Raspberry Pi with a microphone and speaker.
- It uses offline speech recognition with Vosk, so wake/query audio is not sent
  to a speech API.
- It opens Google in a background Chromium page and closes that page after each
  answer.
- It does not store transcripts, cookies, analytics, telemetry, or API keys.
- Google AI Overviews do not appear for every query, every account, or every
  region. Google can also change the page layout, so extraction is best effort.

## Hardware

- Raspberry Pi 4 or newer recommended.
- USB microphone or supported sound card microphone.
- Speaker or audio output supported by Raspberry Pi OS.

## Install

Run these commands on the Pi:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip chromium-browser espeak portaudio19-dev
python3 -m venv ~/snoopy-pi-venv
~/snoopy-pi-venv/bin/pip install --upgrade pip
~/snoopy-pi-venv/bin/pip install -r pi-assistant/requirements.txt
~/snoopy-pi-venv/bin/python -m playwright install chromium
```

Download a small English Vosk model from `https://alphacephei.com/vosk/models`
and unzip it to:

```text
~/snoopy-model
```

The final path should contain files such as `am`, `conf`, and `ivector`.

## Run manually

From the repository folder on the Pi:

```bash
~/snoopy-pi-venv/bin/python pi-assistant/snoopy_pi.py
```

Try either style:

- "hey Snoopy what causes rainbows"
- "hey Snoopy" then wait for "I am listening, Toby" and say "what causes rainbows"

Snoopy sends the exact query words after the wake phrase to Google.

## Run as an always-on service

Copy the service file:

```bash
sudo cp pi-assistant/systemd/snoopy-pi.service /etc/systemd/system/snoopy-pi.service
sudo systemctl daemon-reload
sudo systemctl enable --now snoopy-pi
```

Check logs:

```bash
journalctl -u snoopy-pi -f
```

If your repository or virtual environment is somewhere other than
`/home/pi/snoopy`, edit the paths inside `pi-assistant/systemd/snoopy-pi.service`
before copying it.

## Privacy notes

- Microphone recognition runs locally through Vosk.
- The Google query is sent to Google because Google must receive the search
  words to show an AI Overview.
- Snoopy uses a temporary Chromium profile that is deleted when the process
  exits.
- Snoopy filters unsafe speech words before reading text aloud.
