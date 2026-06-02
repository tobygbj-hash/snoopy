"use strict";

const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition || null;

const elements = {
  activeSpeaker: document.querySelector("#activeSpeaker"),
  clearDataButton: document.querySelector("#clearDataButton"),
  downloadHandoffButton: document.querySelector("#downloadHandoffButton"),
  fallbackLink: document.querySelector("#fallbackLink"),
  fallbackPanel: document.querySelector("#fallbackPanel"),
  fallbackText: document.querySelector("#fallbackText"),
  includeTranscript: document.querySelector("#includeTranscript"),
  indicator: document.querySelector("#listeningIndicator"),
  pageTitle: document.querySelector("#page-title"),
  privacyStatus: document.querySelector("#privacyStatus"),
  requireWakeWord: document.querySelector("#requireWakeWord"),
  searchEngine: document.querySelector("#searchEngine"),
  startButton: document.querySelector("#startButton"),
  statusText: document.querySelector("#statusText"),
  stopButton: document.querySelector("#stopButton"),
  transcriptText: document.querySelector("#transcriptText"),
};

const speechLines = {
  ready: "Hi {name}, I am ready and happy to help.",
  listening: "I am listening now, {name}.",
  awaitingWake:
    "{name}, say a wake phrase like hey Snoopy, then tell me what to search for.",
  wakeAcknowledged: "Hi {name}, I heard you. What should I search for next.",
  noWakeWord:
    "{name}, I did not hear a wake phrase yet. Try hey Snoopy or okay Snoopy.",
  searching: "Wonderful, {name}. I am opening a friendly web search now.",
  blocked: "{name}, your browser wants one extra click to open the results.",
  empty: "{name}, I did not catch a search phrase yet. Please try again.",
  stopped: "All set, {name}. I have stopped listening.",
  stopReady: "{name}, say stop whenever you want me to pause.",
  handoffReady: "{name}, your private handoff file is ready.",
  cleared: "{name}, I cleared the screen details.",
  unsupported:
    "{name}, this browser does not support voice recognition here. You can still type a search in your browser.",
  error: "{name}, I had trouble hearing that. Please try again when you are ready.",
  speakerReady: "Hi {name}, I recognized your voice and I am ready to help.",
};

// Longest phrases first so "wake up snoopy" wins over "hi snoopy".
const wakeWords = [
  "wake up snoopy",
  "attention snoopy",
  "hello snoopy",
  "hey snoopy",
  "hi snoopy",
  "okay snoopy",
  "ok snoopy",
  "yo snoopy",
];

const stopPhrases = ["stop", "stop reading", "please stop", "snoopy stop", "stop listening"];

const engineUrls = {
  bing: "https://www.bing.com/search",
  duckduckgo: "https://duckduckgo.com/",
  google: "https://www.google.com/search",
};

let recognition = null;
let isListening = false;
let shouldRestart = false;
let armedAfterWake = false;
let armedForStop = false;
let lastHeardPhrase = "";
let reservedSearchWindow = null;
let activeProfileId = null;

function getSpeakerCatalog() {
  const catalog = window.SNOOPY_SPEAKER_CATALOG;

  if (!catalog || !catalog.profiles) {
    return {
      defaultProfileId: "toby",
      guestProfileId: "guest",
      profiles: {
        toby: { displayName: "Toby" },
        guest: { displayName: "friend" },
      },
    };
  }

  return catalog;
}

function getProfile(profileId) {
  const catalog = getSpeakerCatalog();
  const profile = catalog.profiles[profileId];

  if (!profile) {
    return catalog.profiles[catalog.guestProfileId || "guest"];
  }

  return profile;
}

function getActiveProfileId() {
  if (activeProfileId) {
    return activeProfileId;
  }

  const catalog = getSpeakerCatalog();
  const params = new URLSearchParams(window.location.search);
  const fromUrl = params.get("listener");

  if (fromUrl && catalog.profiles[fromUrl]) {
    return fromUrl;
  }

  if (elements.activeSpeaker?.value && catalog.profiles[elements.activeSpeaker.value]) {
    return elements.activeSpeaker.value;
  }

  return catalog.defaultProfileId || "toby";
}

function getActiveDisplayName() {
  return getProfile(getActiveProfileId()).displayName;
}

function setActiveProfile(profileId, options = {}) {
  const catalog = getSpeakerCatalog();
  const resolvedId = catalog.profiles[profileId]
    ? profileId
    : catalog.guestProfileId || "guest";

  activeProfileId = resolvedId;

  if (elements.activeSpeaker) {
    elements.activeSpeaker.value = resolvedId;
  }

  updatePersonalizedUi();

  if (options.speakKey) {
    setStatus(options.speakKey);
    speak(options.speakKey);
  }
}

function formatSpeechLine(template) {
  return template.replace(/\{name\}/g, getActiveDisplayName());
}

function setStatus(messageKey) {
  const template = speechLines[messageKey];

  if (!template) {
    return;
  }

  elements.statusText.textContent = formatSpeechLine(template);
}

function speak(messageKey) {
  const template = speechLines[messageKey];

  if (!("speechSynthesis" in window) || !template) {
    return;
  }

  const text = formatSpeechLine(template);

  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "en-US";
  utterance.pitch = 1.12;
  utterance.rate = 0.96;
  utterance.volume = 0.9;

  window.speechSynthesis.speak(utterance);
}

function updatePersonalizedUi() {
  const name = getActiveDisplayName();

  if (elements.pageTitle) {
    elements.pageTitle.textContent = `Hi ${name}, I am Snoopy.`;
  }

  if (elements.privacyStatus && !elements.privacyStatus.dataset.locked) {
    elements.privacyStatus.textContent = `Private mode is on, ${name}. Nothing is stored unless you download a file.`;
  }
}

function isPiListenerMode() {
  const params = new URLSearchParams(window.location.search);
  return params.get("pi") === "1" || params.get("pi") === "true";
}

async function identifySpeakerOnPi() {
  if (!window.SNOOPY_PI_LISTENER?.identifyActiveSpeaker) {
    return null;
  }

  try {
    return await window.SNOOPY_PI_LISTENER.identifyActiveSpeaker();
  } catch (error) {
    return null;
  }
}

function populateSpeakerSelect() {
  if (!elements.activeSpeaker) {
    return;
  }

  const catalog = getSpeakerCatalog();
  const existing = elements.activeSpeaker.value;
  elements.activeSpeaker.textContent = "";

  for (const [profileId, profile] of Object.entries(catalog.profiles)) {
    const option = document.createElement("option");
    option.value = profileId;
    option.textContent = profile.displayName;
    elements.activeSpeaker.append(option);
  }

  elements.activeSpeaker.value = catalog.profiles[existing]
    ? existing
    : getActiveProfileId();
}

function setListeningState(nextIsListening) {
  isListening = nextIsListening;
  elements.startButton.disabled = nextIsListening;
  elements.stopButton.disabled = !nextIsListening;
  elements.indicator.classList.toggle("is-listening", nextIsListening);
}

function normalizeTranscript(transcript) {
  return transcript
    .trim()
    .toLowerCase()
    .replace(/[.,!?;:]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function matchWakeWord(transcript) {
  const normalized = normalizeTranscript(transcript);

  for (const phrase of wakeWords) {
    const pattern = new RegExp(`^${escapeRegExp(phrase)}(?:[\\s,.]|$)`, "i");

    if (!pattern.test(normalized)) {
      continue;
    }

    const remainder = normalized
      .slice(phrase.length)
      .replace(/^[\s,.]+/, "")
      .trim();

    return {
      matched: true,
      wakeWord: phrase,
      remainder,
    };
  }

  return {
    matched: false,
    wakeWord: null,
    remainder: normalized,
  };
}

function stripWakeWords(transcript) {
  let working = transcript.trim();

  for (const phrase of wakeWords) {
    const pattern = new RegExp(`^${escapeRegExp(phrase)}[\\s,.]*`, "i");
    working = working.replace(pattern, "");
  }

  return working.trim();
}

function cleanTranscript(transcript) {
  return stripWakeWords(transcript)
    .replace(/^(please\s+)?(search|find|look up|browse for)\s+/i, "")
    .trim();
}

function requiresWakePhrase() {
  return Boolean(elements.requireWakeWord?.checked);
}

function remainderAfterWakeWords(transcript) {
  let remainder = normalizeTranscript(transcript);

  for (const phrase of wakeWords) {
    if (remainder === phrase) {
      return "";
    }

    const prefix = `${phrase} `;

    if (remainder.startsWith(prefix)) {
      remainder = remainder.slice(prefix.length).trim();
    }
  }

  return remainder;
}

function isStopPhrase(transcript) {
  const normalized = normalizeTranscript(transcript);
  const afterWake = remainderAfterWakeWords(transcript);

  return stopPhrases.includes(normalized) || stopPhrases.includes(afterWake);
}

function isWakePhraseOnly(transcript) {
  return wakeWords.includes(normalizeTranscript(transcript));
}

function setAwaitingWakeVisual(isAwaiting) {
  elements.indicator.classList.toggle("is-awaiting-wake", isAwaiting);
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

  const listenerName = getActiveDisplayName();
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
      <h1>Snoopy is listening, ${listenerName}.</h1>
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
  const name = getActiveDisplayName();
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
  elements.fallbackText.textContent = `${name}, your search was launched. If you need it, this backup button also opens the results.`;
  elements.fallbackPanel.hidden = Boolean(openedWindow);

  setStatus("searching");
  speak("searching");
}

function processSearchQuery(rawTranscript) {
  const query = cleanTranscript(rawTranscript);

  if (!query) {
    setStatus("empty");
    speak("empty");
    return;
  }

  openSearch(query);
}

function handleTranscript(rawTranscript) {
  lastHeardPhrase = rawTranscript || "";
  elements.transcriptText.textContent = rawTranscript || "No words were detected.";

  if (isStopPhrase(rawTranscript)) {
    armedAfterWake = false;
    armedForStop = false;
    setAwaitingWakeVisual(false);
    stopListening();
    return;
  }

  if (isWakePhraseOnly(rawTranscript)) {
    armedAfterWake = false;
    armedForStop = true;
    setAwaitingWakeVisual(true);
    setStatus("stopReady");
    speak("stopReady");
    return;
  }

  if (armedForStop) {
    armedForStop = false;
    setAwaitingWakeVisual(false);

    if (isStopPhrase(rawTranscript)) {
      stopListening();
      return;
    }
  }

  if (!requiresWakePhrase()) {
    processSearchQuery(rawTranscript);
    return;
  }

  const wakeMatch = matchWakeWord(rawTranscript);

  if (wakeMatch.matched) {
    armedAfterWake = false;
    armedForStop = false;
    setAwaitingWakeVisual(false);

    if (wakeMatch.remainder) {
      if (isStopPhrase(wakeMatch.remainder)) {
        stopListening();
        return;
      }

      processSearchQuery(wakeMatch.remainder);
      return;
    }

    armedAfterWake = true;
    setAwaitingWakeVisual(true);
    setStatus("wakeAcknowledged");
    speak("wakeAcknowledged");
    return;
  }

  if (armedAfterWake) {
    armedAfterWake = false;
    setAwaitingWakeVisual(false);

    if (isStopPhrase(rawTranscript)) {
      stopListening();
      return;
    }

    processSearchQuery(rawTranscript);
    return;
  }

  setStatus("noWakeWord");
  speak("noWakeWord");
}

function buildPrivateHandoff() {
  const includeTranscript = elements.includeTranscript.checked;
  const catalog = getSpeakerCatalog();
  const profileId = getActiveProfileId();

  return {
    agentName: "Snoopy",
    ownerName: getActiveDisplayName(),
    activeProfileId: profileId,
    createdAt: new Date().toISOString(),
    purpose: "Private continuity file for moving this voice browsing agent context to a future agent.",
    currentSettings: {
      searchEngine: elements.searchEngine.value,
      activeProfileId: profileId,
      speakerProfiles: catalog.profiles,
      requireWakePhrase: requiresWakePhrase(),
      wakePhrases: [...wakeWords],
      voiceLanguage: recognition ? recognition.lang : "en-US",
      piListenerMode: isPiListenerMode(),
    },
    operatingRules: [
      "Refer to the active listener by their display name using {name} speech templates.",
      "Stay happy, warm, polite, and family friendly.",
      "Do not say swear words.",
      "Only speak from approved assistant response templates.",
      "Open internet searches for spoken requests without reading raw queries aloud.",
      "On Raspberry Pi, identify the speaker locally before searching when voice enrollment is enabled.",
      "When wake phrase mode is on, accept any configured wake phrase before searching.",
    ],
    privacyModel: {
      storesInBrowserStorage: false,
      sendsTelemetry: false,
      usesAnalytics: false,
      microphoneUse: "Only after Start voice agent is pressed and browser permission is granted.",
      voicePrintsStoredOnPiOnly: true,
      transcriptIncluded: includeTranscript,
      transcriptNote: includeTranscript
        ? "The listener explicitly chose to include the last heard phrase."
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
  elements.privacyStatus.dataset.locked = "true";
  elements.privacyStatus.textContent = `${getActiveDisplayName()}, your private handoff file was created on this device only.`;
  setStatus("handoffReady");
  speak("handoffReady");
}

function clearScreenData() {
  lastHeardPhrase = "";
  armedAfterWake = false;
  armedForStop = false;
  setAwaitingWakeVisual(false);
  elements.includeTranscript.checked = false;
  elements.transcriptText.textContent = `Nothing saved, ${getActiveDisplayName()}. Try saying "search sunrise photos".`;
  elements.fallbackPanel.hidden = true;
  elements.fallbackLink.removeAttribute("href");
  elements.privacyStatus.dataset.locked = "true";
  elements.privacyStatus.textContent = `Private mode is on, ${getActiveDisplayName()}. The visible transcript and fallback link were cleared.`;
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
    elements.indicator.classList.toggle("is-listening", true);
    elements.indicator.classList.toggle(
      "is-awaiting-wake",
      requiresWakePhrase() && !armedAfterWake,
    );
  }
}

async function startListening() {
  if (!recognition || isListening) {
    return;
  }

  elements.startButton.disabled = true;

  if (isPiListenerMode()) {
    elements.statusText.textContent = "Listening to who is speaking…";
    const identified = await identifySpeakerOnPi();

    if (identified?.profileId) {
      setActiveProfile(identified.profileId, { speakKey: "speakerReady" });
    } else {
      const catalog = getSpeakerCatalog();
      setActiveProfile(catalog.guestProfileId || "guest", { speakKey: "ready" });
    }
  }

  shouldRestart = true;
  armedAfterWake = false;
  armedForStop = false;
  elements.fallbackPanel.hidden = true;
  reserveSearchWindow();
  setAwaitingWakeVisual(requiresWakePhrase());

  if (requiresWakePhrase()) {
    setStatus("awaitingWake");
    speak("awaitingWake");
  } else {
    setStatus("listening");
    speak("listening");
  }

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
  armedAfterWake = false;
  armedForStop = false;
  setAwaitingWakeVisual(false);

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
    armedAfterWake = false;
    setAwaitingWakeVisual(false);
    closeReservedSearchWindow();
    setListeningState(false);
    setStatus("error");
    speak("error");
  });

  setStatus("ready");
}

async function initializeSpeakerProfiles() {
  if (isPiListenerMode() && window.SNOOPY_PI_LISTENER?.loadCatalog) {
    try {
      await window.SNOOPY_PI_LISTENER.loadCatalog();
    } catch (error) {
      // Fall back to speakers.js defaults when the bridge is not running yet.
    }
  }

  populateSpeakerSelect();
  setActiveProfile(getActiveProfileId());
  setStatus("ready");
}

elements.clearDataButton.addEventListener("click", clearScreenData);
elements.downloadHandoffButton.addEventListener("click", downloadPrivateHandoff);
elements.startButton.addEventListener("click", () => {
  startListening();
});
elements.stopButton.addEventListener("click", stopListening);
elements.activeSpeaker?.addEventListener("change", () => {
  setActiveProfile(elements.activeSpeaker.value, { speakKey: "ready" });
});
elements.requireWakeWord?.addEventListener("change", () => {
  if (!isListening) {
    return;
  }

  armedAfterWake = false;
  setAwaitingWakeVisual(requiresWakePhrase() && !armedAfterWake);
  setStatus(requiresWakePhrase() ? "awaitingWake" : "listening");
});

setupSpeechRecognition();
initializeSpeakerProfiles();
