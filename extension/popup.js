"use strict";

const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition || null;

const queryInput = document.querySelector("#queryInput");
const readSummaryButton = document.querySelector("#readSummaryButton");
const searchAndReadButton = document.querySelector("#searchAndReadButton");
const statusText = document.querySelector("#statusText");
const voiceSearchButton = document.querySelector("#voiceSearchButton");

const messages = {
  ready: "Ready when you are, Toby.",
  listening: "Listening, Toby. Say the exact words to search.",
  searching: "Checking Google in the background, Toby.",
  notGoogle:
    "Toby, please open a Google results page with an AI summary, then try again.",
  noQuery: "Toby, please say or type the exact Google search words first.",
  reading: "Reading the Google AI summary for Toby.",
  unavailable:
    "Toby, I could not reach the current page. Please refresh the Google results page and try again.",
  unsupportedVoice:
    "Toby, this browser does not support voice input in the extension popup.",
};

function setStatus(messageKey) {
  statusText.textContent = messages[messageKey] || messages.unavailable;
}

async function searchGoogleAndReadSummary() {
  const query = queryInput.value.trim();

  if (!query) {
    setStatus("noQuery");
    return;
  }

  setStatus("searching");

  const response = await chrome.runtime.sendMessage({
    type: "SNOOPY_SEARCH_AND_READ_AI_OVERVIEW",
    query,
  });

  if (response?.ok) {
    setStatus("reading");
    return;
  }

  statusText.textContent = response?.message || messages.unavailable;
}

function listenForSearchWords() {
  if (!SpeechRecognition) {
    setStatus("unsupportedVoice");
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = "en-US";

  setStatus("listening");
  recognition.start();

  recognition.addEventListener("result", (event) => {
    const latestResult = event.results[event.results.length - 1];
    const transcript = latestResult[0].transcript.trim();

    queryInput.value = transcript;
    searchGoogleAndReadSummary().catch(() => setStatus("unavailable"));
  });

  recognition.addEventListener("error", () => {
    setStatus("unavailable");
  });
}

async function readCurrentTabSummary() {
  setStatus("ready");

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  if (!tab?.id || !isGoogleResultsPage(tab.url)) {
    setStatus("notGoogle");
    return;
  }

  const response = await sendReadMessage(tab.id);

  if (response?.ok) {
    setStatus("reading");
    return;
  }

  statusText.textContent = response?.message || messages.unavailable;
}

async function sendReadMessage(tabId) {
  try {
    return await chrome.tabs.sendMessage(tabId, {
      type: "SNOOPY_READ_GOOGLE_AI_SUMMARY",
    });
  } catch (error) {
    await chrome.scripting.executeScript({
      target: { tabId },
      files: ["content-script.js"],
    });

    return chrome.tabs.sendMessage(tabId, {
      type: "SNOOPY_READ_GOOGLE_AI_SUMMARY",
    });
  }
}

function isGoogleResultsPage(url = "") {
  try {
    const parsedUrl = new URL(url);
    return parsedUrl.hostname === "www.google.com" && parsedUrl.pathname === "/search";
  } catch (error) {
    return false;
  }
}

searchAndReadButton.addEventListener("click", () => {
  searchGoogleAndReadSummary().catch(() => setStatus("unavailable"));
});

voiceSearchButton.addEventListener("click", listenForSearchWords);

readSummaryButton.addEventListener("click", () => {
  readCurrentTabSummary().catch(() => setStatus("unavailable"));
});
