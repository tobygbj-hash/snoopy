# Snoopy

Snoopy is a cheerful, polite voice-activated browsing agent for Toby. It listens
for spoken words in the browser, turns them into a web search, and opens the
results in a new tab.

**Documentation:** [docs/README.md](docs/README.md) (operations, architecture,
commits, Raspberry Pi notes). **Contributing:** [CONTRIBUTING.md](CONTRIBUTING.md).

## Features

- Voice activation through the browser Web Speech API.
- Warm, happy responses that use each listener's name (Toby, Mum, etc.).
- **Raspberry Pi:** local voice enrollment so Snoopy recognizes who is speaking — see [docs/SPEAKER-PROFILES.md](docs/SPEAKER-PROFILES.md).
- Internet browsing by opening Google searches for spoken queries.
- Safe assistant speech: Snoopy only speaks from approved polite phrases and
  never reads raw search terms aloud.
- Private handoff download for transferring operating notes to a future agent.
- No server, analytics, telemetry, API key, or persistent browser storage required.

## Raspberry Pi (laptop off, Pi in the room)

**Keep it simple:** start with **[pi/MVP.md](pi/MVP.md)** (reminders + speaker, no browser).

Full Pi guide (optional kiosk, extension): **[pi/README.md](pi/README.md)**.

## Run locally

**Important:** Do not double-click `index.html`. Run a local server, then open the link:

```bash
npm run serve
```

Open **http://localhost:8000** in Chrome.

Or use the hosted copy: **https://tobygbj-hash.github.io/snoopy/**

If the page does not load, see **[docs/START.md](docs/START.md)**.

<details>
<summary>Other ways to serve the folder</summary>

Open `index.html` in a modern browser only after starting a server, or serve the folder:

```bash
npm run serve
```

Then visit `http://localhost:8000`.

Equivalent: `python3 -m http.server 8000`.

Microphone access and speech recognition support depend on the browser. Chrome
and Edge provide the broadest Web Speech API support.

</details>

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
2. Leave **Require a wake phrase** on (recommended) or turn it off for immediate
   search without a wake phrase.
3. Click **Start voice agent** and allow microphone access.
4. With wake phrase mode on, start with any eligible wake phrase, then say what
   to search for (in one sentence or two steps):
   - "hey Snoopy, find beginner piano lessons"
   - "hi Snoopy" … then "search cheerful dog pictures"
   - "okay Snoopy, look up local weather"
   - "wake up Snoopy, search sunrise photos"
   - "hello Snoopy" or "attention Snoopy" also work
5. Snoopy reserves a results tab, sends the spoken words to the selected search
   engine, and confirms with a warm message for Toby.

Eligible wake phrases are listed on the Snoopy page under **Wake phrases Toby can use**.

Snoopy keeps a backup button available in case the browser does not switch to
the results tab automatically.

## Read Google AI summaries aloud (no extension required)

If your school or work Chrome account **blocks extensions**, use the
**bookmarklet** instead. You do not need Developer Mode.

### Bookmarklet setup (recommended for Toby)

1. Run Snoopy locally (`npm run serve`) or open your GitHub Pages URL.
2. Open **`summary-bookmarklet.html`** (for example `http://localhost:8000/summary-bookmarklet.html`).
3. Show the bookmarks bar: **Ctrl+Shift+B** (Windows) or **Cmd+Shift+B** (Mac).
4. Drag the orange **Read AI summary** link onto the bookmarks bar.
5. Open a Google results page that shows an **AI Overview**.
6. Click the bookmark. Snoopy reads the summary aloud for Toby.
7. While it is reading, say **stop** or **hey Snoopy, stop** to stop with a kind reply.

Allow the microphone on `google.com` if Chrome asks — Snoopy only listens for stop
and wake phrases while the summary is playing.

The bookmarklet does not use a backend, storage, or a new tab. If bookmarklets are
blocked too, only your account administrator can change that policy.

### Optional: Chrome extension

If Developer Mode is allowed, you can use the `extension` folder instead of the
bookmarklet. See `extension/README.md`.

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

## For maintainers

| Task | Command or doc |
| ---- | ---------------- |
| Run policy tests | `npm test` |
| Local server | `npm run serve` |
| Operations and deploy | [docs/OPERATIONS.md](docs/OPERATIONS.md) |
| Commit message format | [docs/COMMITS.md](docs/COMMITS.md) or [COMMITS.md](COMMITS.md) |
| AI agent rules | [AGENTS.md](AGENTS.md) |
