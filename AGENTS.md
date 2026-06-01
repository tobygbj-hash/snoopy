# Instructions for AI coding agents

This repository is **Snoopy**: a warm, privacy-first voice browsing agent for
**Toby**. Follow these rules when editing code or opening pull requests.

## Non-negotiable product rules

1. **Address the user as Toby** in all spoken assistant lines.
2. **Speech safety:** Assistant audio must use only approved templates in
   `speechLines` (in `app.js` or equivalent). Never speak raw search queries or
   unfiltered page text without the same filtering the extension uses.
3. **No backend** for the core app: no server, API keys, analytics, or telemetry.
4. **No persistent browser storage** in app/extension/bookmarklet code:
   no `localStorage`, `sessionStorage`, or `document.cookie`.
5. **No network from app code:** no `fetch`, `XMLHttpRequest`, or `sendBeacon` in
   browser-facing JavaScript (search happens by navigating to the search engine).
6. **CSP:** Keep `connect-src 'none'` on `index.html` and `summary-bookmarklet.html`.
7. **Extension scope:** `host_permissions` must stay `https://www.google.com/*` only.
   No background service worker; no `storage` permission.

## Before you finish

```bash
npm test
```

Fix any failure from `scripts/check-agent-policy.js` before committing.

## Where to change things

| Goal | Files |
| ---- | ----- |
| Voice search behavior | `app.js`, `index.html` |
| Approved spoken replies | `speechLines` in `app.js` |
| Google summary reading | `extension/content-script.js`, `summary-bookmarklet.js` |
| Deployed site | `index.html`, `app.js`, `styles.css`, bookmarklet files; workflow in `.github/workflows/pages.yml` |
| Policy rules | `scripts/check-agent-policy.js` |

## Documentation

- [docs/README.md](docs/README.md) — documentation index
- [docs/OPERATIONS.md](docs/OPERATIONS.md) — run, test, deploy
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — system overview
- [docs/COMMITS.md](docs/COMMITS.md) — commit message format

## Git workflow

- Branch from `main`: `cursor/<description>-0c8f` (lowercase).
- Commit using [docs/COMMITS.md](docs/COMMITS.md).
- Do not weaken privacy checks to make tests pass; adjust code to comply.

## Private handoff

Handoff JSON is generated in the browser for continuity. Do not add features that
upload handoff data automatically.
