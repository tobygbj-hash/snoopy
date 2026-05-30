# Snoopy

Snoopy is a cheerful, polite voice-activated browsing agent for Toby. It listens
for spoken words in the browser, turns them into a web search, and opens the
results in a new tab.

## Features

- Voice activation through the browser Web Speech API.
- Warm, happy responses that refer to the user as Toby.
- Internet browsing by opening DuckDuckGo searches for spoken queries.
- Safe assistant speech: Snoopy only speaks from approved polite phrases and
  never reads raw search terms aloud.
- Private handoff download for transferring operating notes to a future agent.
- No server, analytics, telemetry, API key, or persistent browser storage required.

## Run locally

Open `index.html` in a modern browser, or serve the folder with any static file
server:

```bash
python3 -m http.server 8000
```

Then visit `http://localhost:8000`.

Microphone access and speech recognition support depend on the browser. Chrome
and Edge provide the broadest Web Speech API support.

## How to use

1. Select a search engine if you want something other than DuckDuckGo.
2. Click **Start voice agent** and allow microphone access.
3. Say what you want to search for, such as:
   - "search cheerful dog pictures"
   - "look up local weather"
   - "hey Snoopy, find beginner piano lessons"
4. Snoopy opens a results tab and confirms with a warm message for Toby.

If the browser blocks popups, Snoopy shows a button you can click to open the
results.

## Private handoff

Use **Download private handoff** when you want to transfer Snoopy's operating
rules and current settings to another agent. The handoff file is created locally
in the browser. It does not include the last heard phrase unless Toby explicitly
checks **Include the last heard phrase in the handoff file** first.

Use **Clear screen data** before stepping away or sharing the screen. This clears
the visible transcript and fallback search link.

## Security and privacy notes

- Snoopy is a static app and does not run a backend server.
- The app does not use `localStorage`, `sessionStorage`, cookies, analytics,
  telemetry, `fetch`, or beacon calls.
- A Content Security Policy limits loading to same-origin app files and blocks
  network connections from the app code.
- A no-referrer policy and `noopener noreferrer` links reduce browser referrer
  and opener leaks when search results open.
- Search phrases are sent to the chosen search engine because that is necessary
  to browse for the spoken words. DuckDuckGo is the default search engine.
- Microphone access is controlled by the browser and only starts after Toby
  clicks **Start voice agent** and grants permission.
