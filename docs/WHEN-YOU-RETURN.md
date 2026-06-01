# When you return — Snoopy work in progress

Last updated for branches pushed to GitHub. Your laptop can be off; everything below is on the remote repo.

## Open pull requests to review

| PR | Branch | What it does |
| -- | ------ | ------------ |
| [#12](https://github.com/tobygbj-hash/snoopy/pull/12) | `cursor/docs-and-operations-0c8f` | Docs hub, commit guide, `npm run serve`, AGENTS.md |
| [#13](https://github.com/tobygbj-hash/snoopy/pull/13) | `cursor/multi-wake-words-0c8f` | Multiple wake phrases (hey/hi/okay Snoopy, etc.) |
| [#14](https://github.com/tobygbj-hash/snoopy/pull/14) | `cursor/pi-appliance-guide-0c8f` | Pi setup guide, systemd, kiosk, Bluetooth notes |

Merge order suggestion: **#12** → **#13** → **#14** (or #13 before #12 if you only care about wake words first).

## Quick test on your laptop (Chrome)

```bash
git clone https://github.com/tobygbj-hash/snoopy.git
cd snoopy
git checkout cursor/multi-wake-words-0c8f   # wake phrases
npm run serve
```

Open http://localhost:8000 — allow mic — try “Hey Snoopy, find calm music”.

## Pi plan (laptop not in the room)

Read **[pi/README.md](../pi/README.md)** on branch `cursor/pi-appliance-guide-0c8f`:

- Pi runs Snoopy + Chromium + extension
- **USB mic** + **Bluetooth speaker** supported
- systemd + kiosk autostart included

## Verify no errors

```bash
npm test
```

All branches with new code should pass this before merge.

## Bluetooth + mic (short answer)

Yes: plug a **USB microphone** into the Pi, pair a **Bluetooth speaker** as the system default output, then use Snoopy in Chromium on the Pi as usual.

## Repo

https://github.com/tobygbj-hash/snoopy
