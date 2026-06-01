# Raspberry Pi roadmap

Snoopy today runs in the browser. A Raspberry Pi can turn it into a
Google Home–style appliance without changing the privacy model (everything can
stay on your LAN).

This document is planning notes only; nothing here is required to run the
current project.

## Phase 1: Kiosk appliance (lowest effort)

- Raspberry Pi OS + Chromium kiosk → full-screen Snoopy (`index.html`)
- USB mic and speaker (or Bluetooth audio)
- Optional GPIO LED when listening; optional button for push-to-talk
- Serve from GitHub Pages or `npm run serve` on the Pi at boot

## Phase 2: Wake word

- Local wake-word daemon (e.g. openWakeWord) for "Hey Snoopy"
- On wake: focus kiosk tab and trigger Start, or send phrase to the same search
  flow as `app.js`

## Phase 3: Read summaries in the room

- Chromium with the Snoopy extension loaded
- Voice search → Google results → **Read AI summary** automatically or by voice
  command

## Phase 4: Offline voice (optional)

- Whisper STT + Piper TTS on the Pi
- Keep approved phrase list for confirmations; only read filtered summary text

## Phase 5: Smart home (optional)

- Home Assistant on LAN; Pi routes intents like "turn off the light"
- Keep browsing and home control as separate skills

## Suggested `pi/` folder (future)

When implementation starts, a `pi/` directory might contain:

- `kiosk-autostart.desktop` — Chromium on login
- `install.sh` — packages and autostart
- `README.md` — hardware list and wiring notes

Until then, use [OPERATIONS.md](OPERATIONS.md) for the browser-based setup.
