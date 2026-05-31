"use strict";

const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition || null;

const elements = {
  clearDataButton: document.querySelector("#clearDataButton"),
  downloadHandoffButton: document.querySelector("#downloadHandoffButton"),
  fallbackLink: document.querySelector("#fallbackLink"),
  fallbackPanel: document.querySelector("#fallbackPanel"),
  fallbackText: document.querySelector("#fallbackText"),
  includeTranscript: document.querySelector("#includeTranscript"),
  indicator: document.querySelector("#listeningIndicator"),
  privacyStatus: document.querySelector("#privacyStatus"),
  searchEngine: document.querySelector("#searchEngine"),
  startButton: document.querySelector("#startButton"),
  statusText: document.querySelector("#statusText"),
  stopButton: document.querySelector("#stopButton"),
  transcriptText: document.querySelector("#transcriptText"),
};

const speechLines = {
  ready: "Hi Toby, I am ready and happy to help.",
  listening: "I am listening now, Toby.",
  searching: "Wonderful, Toby. I am opening a friendly web search now.",
  blocked: "Toby, your browser wants one extra click to open the results.",
  empty: "Toby, I did not catch a search phrase yet. Please try again.",
  stopped: "All set, Toby. I have stopped listening.",
  handoffReady: "Toby, your private handoff file is ready.",
  cleared: "Toby, I cleared the screen details.",
  unsupported:
    "Toby, this browser does not support voice recognition here. You can still type a search in your browser.",
  error: "Toby, I had trouble hearing that. Please try again when you are ready.",
};

const engineUrls = {
  bing: "https://www.bing.com/search",
  duckduckgo: "https://duckduckgo.com/",
  google: "https://www.google.com/search",
};

let recognition = null;
let isListening = false;
let shouldRestart = false;
let lastHeardPhrase = "";
let reservedSearchWindow = null;

function setStatus(messageKey) {
  elements.statusText.textContent = speechLines[messageKey];
}

function speak(messageKey) {
  const text = speechLines[messageKey];

  if (!("speechSynthesis" in window) || !text) {
    return;
  }

  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "en-US";
  utterance.pitch = 1.12;
  utterance.rate = 0.96;
  utterance.volume = 0.9;

  window.speechSynthesis.speak(utterance);
}

function setListeningState(nextIsListening) {
  isListening = nextIsListening;
  elements.startButton.disabled = nextIsListening;
  elements.stopButton.disabled = !nextIsListening;
  elements.indicator.classList.toggle("is-listening", nextIsListening);
}

function cleanTranscript(transcript) {
  return transcript
    .trim()
    .replace(/^hey\s+snoopy[\s,]*/i, "")
    .replace(/^(please\s+)?(search|find|look up|browse for)\s+/i, "")
    .trim();
}

function buildSearchUrl(query) {
  const engine = elements.searchEngine.value;
  const url = new URL(engineUrls[engine] || engineUrls.google);
  url.searchParams.set("q", query);
  return url.toString();
}

function closeReservedSearchWindow() {
  if (reservedSearchWindow && !reservedSearchWindow.closed) {
    reservedSearchWindow.close();
  }

  reservedSearchWindow = null;
}

function reserveSearchWindow() {
  if (reservedSearchWindow && !reservedSearchWindow.closed) {
    return true;
  }

  reservedSearchWindow = window.open("", "snoopy-search-results");

  if (!reservedSearchWindow) {
    return false;
  }

  try {
    reservedSearchWindow.opener = null;
    reservedSearchWindow.document.open();
    reservedSearchWindow.document.write(`<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="referrer" content="no-referrer" />
    <title>Snoopy is listening</title>
    <style>
      body {
        min-height: 100vh;
        margin: 0;
        display: grid;
        place-items: center;
        background: #fff8ec;
        color: #2f2924;
        font-family: system-ui, sans-serif;
      }
      main {
        max-width: 38rem;
        padding: 2rem;
        text-align: center;
      }
    </style>
  </head>
  <body>
    <main>
      <h1>Snoopy is listening, Toby.</h1>
      <p>Your search results will appear here after you speak.</p>
    </main>
  </body>
</html>`);
    reservedSearchWindow.document.close();
    window.focus();
  } catch (error) {
    reservedSearchWindow = null;
    return false;
  }

  return true;
}

function openSearch(query) {
  const searchUrl = buildSearchUrl(query);
  let openedWindow = null;

  if (reservedSearchWindow && !reservedSearchWindow.closed) {
    try {
      reservedSearchWindow.location.replace(searchUrl);
      openedWindow = reservedSearchWindow;
      reservedSearchWindow = null;
    } catch (error) {
      openedWindow = null;
    }
  }

  if (!openedWindow) {
    openedWindow = window.open(searchUrl, "_blank", "noopener,noreferrer");
  }

  elements.fallbackLink.href = searchUrl;
  elements.fallbackText.textContent =
    "Toby, your search was launched. If you need it, this backup button also opens the results.";
  elements.fallbackPanel.hidden = Boolean(openedWindow);

  setStatus("searching");
  speak("searching");
}

function handleTranscript(rawTranscript) {
  const query = cleanTranscript(rawTranscript);

  lastHeardPhrase = rawTranscript || "";
  elements.transcriptText.textContent = rawTranscript || "No words were detected.";

  if (!query) {
    setStatus("empty");
    speak("empty");
    return;
  }

  openSearch(query);
}


function buildPrivateHandoff() {
  const includeTranscript = elements.includeTranscript.checked;

  return {
    agentName: "Snoopy",
    ownerName: "Toby",
    createdAt: new Date().toISOString(),
    purpose: "Private continuity file for moving this voice browsing agent context to a future agent.",
    currentSettings: {
      searchEngine: elements.searchEngine.value,
      voiceLanguage: recognition ? recognition.lang : "en-US",
    },
    operatingRules: [
      "Refer to the user as Toby.",
      "Stay happy, warm, polite, and family friendly.",
      "Do not say swear words.",
      "Only speak from approved assistant response templates.",
      "Open internet searches for spoken requests without reading raw queries aloud.",
    ],
    privacyModel: {
      storesInBrowserStorage: false,
      sendsTelemetry: false,
      usesAnalytics: false,
      microphoneUse: "Only after Toby presses Start voice agent and grants browser permission.",
      transcriptIncluded: includeTranscript,
      transcriptNote: includeTranscript
        ? "Toby explicitly chose to include the last heard phrase."
        : "Transcript omitted by default for privacy.",
    },
    lastHeardPhrase: includeTranscript ? lastHeardPhrase : null,
  };
}

function downloadPrivateHandoff() {
  const payload = buildPrivateHandoff();
  const blob = new Blob([JSON.stringify(payload, null, 2)], {
    type: "application/json",
  });
  const handoffUrl = URL.createObjectURL(blob);
  const downloadLink = document.createElement("a");

  downloadLink.href = handoffUrl;
  downloadLink.download = `snoopy-private-handoff-${new Date()
    .toISOString()
    .slice(0, 10)}.json`;
  downloadLink.rel = "noopener noreferrer";
  document.body.append(downloadLink);
  downloadLink.click();
  downloadLink.remove();

  window.setTimeout(() => URL.revokeObjectURL(handoffUrl), 0);
  elements.privacyStatus.textContent =
    "Toby, your private handoff file was created on this device only.";
  setStatus("handoffReady");
  speak("handoffReady");
}

function clearScreenData() {
  lastHeardPhrase = "";
  elements.includeTranscript.checked = false;
  elements.transcriptText.textContent =
    'Nothing saved, Toby. Try saying "search sunrise photos".';
  elements.fallbackPanel.hidden = true;
  elements.fallbackLink.removeAttribute("href");
  elements.privacyStatus.textContent =
    "Private mode is on, Toby. The visible transcript and fallback link were cleared.";
  setStatus("cleared");
  speak("cleared");
}

function handleRecognitionResult(event) {
  const latestResult = event.results[event.results.length - 1];

  if (!latestResult.isFinal) {
    return;
  }

  handleTranscript(latestResult[0].transcript);
}

function handleRecognitionEnd() {
  setListeningState(false);

  if (shouldRestart) {
    recognition.start();
    setListeningState(true);
  }
}

function startListening() {
  if (!recognition || isListening) {
    return;
  }

  shouldRestart = true;
  elements.fallbackPanel.hidden = true;
  reserveSearchWindow();
  setStatus("listening");
  speak("listening");

  try {
    recognition.start();
    setListeningState(true);
  } catch (error) {
    shouldRestart = false;
    closeReservedSearchWindow();
    setListeningState(false);
    setStatus("error");
    speak("error");
  }
}

function stopListening() {
  shouldRestart = false;

  if (recognition && isListening) {
    recognition.stop();
  }

  closeReservedSearchWindow();
  setListeningState(false);
  setStatus("stopped");
  speak("stopped");
}

function setupSpeechRecognition() {
  if (!SpeechRecognition) {
    elements.startButton.disabled = true;
    setStatus("unsupported");
    return;
  }

  recognition = new SpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = false;
  recognition.lang = "en-US";

  recognition.addEventListener("result", handleRecognitionResult);
  recognition.addEventListener("end", handleRecognitionEnd);
  recognition.addEventListener("error", () => {
    shouldRestart = false;
    closeReservedSearchWindow();
    setListeningState(false);
    setStatus("error");
    speak("error");
  });

  setStatus("ready");
}

elements.clearDataButton.addEventListener("click", clearScreenData);
elements.downloadHandoffButton.addEventListener("click", downloadPrivateHandoff);
elements.startButton.addEventListener("click", startListening);
elements.stopButton.addEventListener("click", stopListening);

setupSpeechRecognition();
