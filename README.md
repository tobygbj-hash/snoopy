# Snoopy

Snoopy is a cheerful, polite voice-activated browsing agent for Toby. It listens
for spoken words in the browser, turns them into a web search, and opens the
results in a new tab.

## Features

- Voice activation through the browser Web Speech API.
- Warm, happy responses that refer to the user as Toby.
- Internet browsing by opening Google searches for spoken queries.
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

## Use without local hosting

This repo includes a GitHub Pages workflow at `.github/workflows/pages.yml`.
After the changes are merged to `main`, the repo owner can make the voice agent
available from GitHub without running anything locally:

1. Open the repository on GitHub.
2. Go to **Settings** -> **Pages**.
3. Set **Source** to **GitHub Actions**.
4. Run the **Deploy voice agent to GitHub Pages** workflow, or push to `main`.

The workflow deploys only `index.html`, `app.js`, and `styles.css`.

Privacy note: a normal GitHub Pages site can be reachable by anyone with the
site URL, even when the source repository is private. If the agent must be
restricted to only you, use a private hosting option with sign-in protection
instead of a public Pages URL.

## How to use

1. Select a search engine if you want something other than Google.
2. Click **Start voice agent** and allow microphone access.
3. Say what you want to search for, such as:
   - "search cheerful dog pictures"
   - "look up local weather"
   - "hey Snoopy, find beginner piano lessons"
4. Snoopy reserves a results tab, sends the spoken words to the selected search
   engine, and confirms with a warm message for Toby.

Snoopy keeps a backup button available in case the browser does not switch to
the results tab automatically.


## Always-on Raspberry Pi assistant

For a Google Home-style setup that can keep running without your computer, use
the `pi-assistant` folder. This version runs on a Raspberry Pi with a microphone
and speaker. It listens for "hey Snoopy", sends the exact spoken query words to
Google, tries to read the AI Overview, and speaks the summary aloud.

Quick path:

1. Put this repo on the Raspberry Pi.
2. Follow `pi-assistant/README.md` to install Vosk, Chromium, and the Python
   dependencies.
3. Run `~/snoopy-pi-venv/bin/python pi-assistant/snoopy_pi.py`.
4. For always-on use, install `pi-assistant/systemd/snoopy-pi.service`.

Notes: speech recognition runs locally on the Pi, but the query text is sent to
Google because Google needs it to produce search results and an AI Overview. AI
Overviews are best effort because Google may not show one for every search.

## Read Google AI summaries aloud

The `extension` folder contains a Chrome extension for reading Google AI
summaries aloud from the current Google results tab. It does not open a new tab.

To install it for free:

1. Download this repository from GitHub, or clone it.
2. Open Chrome and go to `chrome://extensions`.
3. Turn on **Developer mode**.
4. Click **Load unpacked**.
5. Select the `extension` folder.

Then open a Google results page with an AI summary and click **Read AI
summary**. Snoopy reads the summary aloud for Toby in the same tab.


## If Chrome blocks Developer Mode

Some managed accounts do not allow unpacked extensions. In that case, use the
no-extension bookmarklet instead:

1. Open `summary-bookmarklet.html` from the Snoopy site.
2. Show Chrome's bookmarks bar with **Ctrl+Shift+B**.
3. Drag **Read AI summary** to the bookmarks bar.
4. Open a Google results page with an AI summary.
5. Click the bookmark to have Snoopy read the summary aloud in the same tab.

The bookmarklet does not store data, use a backend, or open a new tab. If your
managed account blocks bookmarklets too, only the account administrator can
change that setting.

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
  to browse for the spoken words. Google is the default search engine.
- Microphone access is controlled by the browser and only starts after Toby
  clicks **Start voice agent** and grants permission.
