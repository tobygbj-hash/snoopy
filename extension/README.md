# Snoopy Google Summary Reader

This Chrome extension lets Snoopy read a Google AI summary aloud from the
current Google results tab. It does not open a new tab.

## Install in Chrome

1. Download this repository from GitHub, or clone it.
2. Open Chrome and go to `chrome://extensions`.
3. Turn on **Developer mode**.
4. Click **Load unpacked**.
5. Select the `extension` folder.

## Use

1. Open a Google results page that shows an AI summary.
2. Click the floating **Read AI summary** button, or click the Snoopy extension
   icon and then **Read summary aloud**.
3. Snoopy reads a short version of the AI summary in the same tab.
4. While Snoopy is reading, say **stop** (or **stop reading**) to stop immediately.

Allow the microphone on `google.com` if Chrome asks — Snoopy only listens for the
word stop while a summary is playing. Nothing is recorded or sent to a server.

## Privacy and safety

- The extension only asks for access to `https://www.google.com/*`.
- It does not use storage, cookies, analytics, telemetry, `fetch`, beacons, or a
  backend server.
- It reads visible text from the current Google tab and sends it only to the
  browser's built-in speech synthesis.
- Snoopy adds a warm Toby-focused introduction and filters unsafe speech words
  before reading the summary aloud.

Google can change the AI summary page structure at any time. If Snoopy cannot
find the summary, refresh the Google results page and try again.
