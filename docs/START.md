# Start Snoopy (fix “page isn’t working”)

## Use one of these URLs

| Method | URL |
| ------ | --- |
| **On your laptop (recommended)** | http://localhost:8000 |
| **Online (no install)** | https://tobygbj-hash.github.io/snoopy/ |
| **Bookmarklet setup** | http://localhost:8000/summary-bookmarklet.html or add `/summary-bookmarklet.html` to the GitHub Pages link above |

## Local setup (first time)

```bash
git clone https://github.com/tobygbj-hash/snoopy.git
cd snoopy
npm run serve
```

Keep the terminal open. Open **http://localhost:8000** in Chrome.

Do **not** double-click `index.html` in Finder or File Explorer — that uses `file://` and the page will not work properly.

## “This site can’t be reached” / blank page

| Cause | Fix |
| ----- | --- |
| `npm run serve` not running | Run it in the `snoopy` folder and leave the window open |
| Wrong address | Use `http://localhost:8000` not `https://localhost:8000` unless you know otherwise |
| Opened the file directly | Use `npm run serve` or GitHub Pages instead |
| GitHub Pages 404 | Use the full path: `https://tobygbj-hash.github.io/snoopy/` (includes `/snoopy/`) |

## No Chrome extension?

Use the bookmarklet: [summary-bookmarklet.html](../summary-bookmarklet.html) — see [README](../README.md).

## Still stuck?

Run `npm test` in the repo folder — it should say policy checks passed.
