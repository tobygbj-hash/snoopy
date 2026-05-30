"use strict";

const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition || null;

const elements = {
  fallbackLink: document.querySelector("#fallbackLink"),
  fallbackPanel: document.querySelector("#fallbackPanel"),
  fallbackText: document.querySelector("#fallbackText"),
  indicator: document.querySelector("#listeningIndicator"),
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
  const url = new URL(engineUrls[engine] || engineUrls.duckduckgo);
  url.searchParams.set("q", query);
  return url.toString();
}

function openSearch(query) {
  const searchUrl = buildSearchUrl(query);
  const openedWindow = window.open(searchUrl, "_blank", "noopener,noreferrer");

  elements.fallbackLink.href = searchUrl;
  elements.fallbackText.textContent =
    "Toby, if the new tab did not open, this button will take you to the search results.";
  elements.fallbackPanel.hidden = Boolean(openedWindow);

  setStatus("searching");
  speak("searching");
}

function handleTranscript(rawTranscript) {
  const query = cleanTranscript(rawTranscript);

  elements.transcriptText.textContent = rawTranscript || "No words were detected.";

  if (!query) {
    setStatus("empty");
    speak("empty");
    return;
  }

  openSearch(query);
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
  setStatus("listening");
  speak("listening");

  try {
    recognition.start();
    setListeningState(true);
  } catch (error) {
    shouldRestart = false;
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
    setListeningState(false);
    setStatus("error");
    speak("error");
  });

  setStatus("ready");
}

elements.startButton.addEventListener("click", startListening);
elements.stopButton.addEventListener("click", stopListening);

setupSpeechRecognition();
