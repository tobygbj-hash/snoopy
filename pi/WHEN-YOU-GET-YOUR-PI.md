# When your Raspberry Pi arrives

**Start here:** [MVP.md](MVP.md) — one short path, optional steps clearly marked.

You do **not** need Chromium, the extension, or a laptop in the room for reminders.

## Minimum checklist

1. Flash Raspberry Pi OS + Wi‑Fi ([README.md](README.md) Phase 1).
2. Follow **[MVP.md](MVP.md)** — install `snoopy-scheduler`, hear one test reminder.
3. Enroll voices only if more than one person will use it.
4. Add phone calendars later if you want them.

## Verify the repo (no Pi required)

On any computer:

```bash
git clone https://github.com/tobygbj-hash/snoopy.git
cd snoopy
npm test
```

## Zane

Your RC car project can stay on the same Pi; scheduling does not use GPIO.
