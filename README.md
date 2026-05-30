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
- No server or API key required.

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
