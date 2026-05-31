# Snoopy Google Summary Reader

This Chrome extension lets Snoopy search Google in the background, read the AI
Overview aloud for Toby, and close the background tab without switching to it. It
can also read a Google AI summary from the current Google results tab.

## Install in Chrome

1. Download this repository from GitHub, or clone it.
2. Open Chrome and go to `chrome://extensions`.
3. Turn on **Developer mode**.
4. Click **Load unpacked**.
5. Select the `extension` folder.

## Use

### Search in the background

1. Click the Snoopy extension icon.
2. Click **Speak search words**, or type the exact Google search words.
3. Click **Search Google and read AI Overview**.
4. Snoopy opens Google in an inactive tab, reads the AI Overview aloud, and
   closes that tab without switching you to it.

### Read the current Google page

1. Open a Google results page that shows an AI summary.
2. Click the floating **Read AI summary** button, or click the Snoopy extension
   icon and then **Read summary aloud**.
3. Snoopy reads a short version of the AI summary in the same tab.

## Privacy and safety

- The extension only asks for access to `https://www.google.com/*`.
- It asks for `tabs`, `scripting`, and `tts` so it can open an inactive Google
  results tab, read the AI Overview, close the tab, and speak through Chrome.
- It does not use storage, cookies, analytics, telemetry, `fetch`, beacons, or a
  backend server.
- It reads visible text from Google pages and sends it only to Chrome's built-in
  text-to-speech.
- Snoopy adds a warm Toby-focused introduction and filters unsafe speech words
  before reading the summary aloud.

Google can change the AI summary page structure at any time. If Snoopy cannot
find the summary, refresh the Google results page and try again.
