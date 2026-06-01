# Operations guide

Day-to-day steps for running, verifying, and shipping Snoopy.

## Prerequisites

- A modern browser (Chrome or Edge recommended for Web Speech API)
- [Node.js](https://nodejs.org/) 18+ for policy checks (CI uses Node 22)
- Microphone permission when using voice features

## Run locally

### Option A: npm script

```bash
npm run serve
```

Open `http://localhost:8000` in the browser.

### Option B: Python

```bash
python3 -m http.server 8000
```

### Option C: Open the file directly

Opening `index.html` as a `file://` URL may work, but some browsers restrict
speech recognition or pop-up windows on file URLs. Prefer a local server.

## Install the Chrome extension

1. Clone or download this repository.
2. Open `chrome://extensions`.
3. Enable **Developer mode**.
4. Click **Load unpacked** and select the `extension` folder.

Details: [extension/README.md](../extension/README.md).

## Use the bookmarklet (no extension)

1. Serve the repo locally or use the deployed GitHub Pages site.
2. Open `summary-bookmarklet.html`.
3. Drag **Read AI summary** to the bookmarks bar.
4. On a Google results page with an AI summary, click the bookmark.

## Run tests

```bash
npm test
```

This runs:

- `node --check` on `app.js`, extension scripts, and `summary-bookmarklet.js`
- `node scripts/check-agent-policy.js` (speech lines, CSP, privacy rules)

Run tests before every commit that touches browser code or HTML.

## Deploy to GitHub Pages

The workflow `.github/workflows/pages.yml` runs on push to `main` and on manual
dispatch.

**One-time GitHub setup:**

1. Repository **Settings** → **Pages**
2. **Source**: **GitHub Actions**
3. Merge to `main` or run **Deploy voice agent to GitHub Pages**

**Deployed files:** `index.html`, `app.js`, `styles.css`, `summary-bookmarklet.html`,
`summary-bookmarklet.js` (built into `dist/` in CI).

The extension is **not** deployed to Pages; it is loaded unpacked from the repo.

## Troubleshooting

| Symptom | Likely cause | What to try |
| ------- | ------------- | ----------- |
| Start button disabled | Browser lacks Web Speech API | Use Chrome or Edge |
| No speech heard | Tab muted or OS volume | Check system and tab audio |
| Results tab blocked | Pop-up blocker | Allow pop-ups for the Snoopy origin; use fallback link |
| Extension cannot find summary | Google changed page HTML | Refresh results page; update selectors in `content-script.js` |
| `npm test` fails on speech line | New `speak("key")` without `speechLines` entry | Add approved line in `app.js` (must include "Toby") |
| Policy check fails on `fetch` | Accidental network call | Remove; Snoopy must stay offline in app code |

## Clear screen before sharing

On the live app, use **Clear screen data** before screen sharing. This removes
the visible transcript and fallback search link from the page (nothing is
stored in browser storage).

## Private handoff files

**Download private handoff** creates a JSON file on the device only. It does not
upload anywhere. By default it omits the last heard phrase unless Toby checks
**Include the last heard phrase in the handoff file**.

## Optional: git commit template

To use the repo commit message template:

```bash
git config commit.template .gitmessage
```

See [COMMITS.md](COMMITS.md) for message format.
