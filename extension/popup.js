"use strict";

const readSummaryButton = document.querySelector("#readSummaryButton");
const statusText = document.querySelector("#statusText");

const messages = {
  ready: "Ready when you are, Toby.",
  notGoogle:
    "Toby, please open a Google results page with an AI summary, then try again.",
  reading: "Reading the Google AI summary for Toby.",
  unavailable:
    "Toby, I could not reach the current page. Please refresh the Google results page and try again.",
};

function setStatus(messageKey) {
  statusText.textContent = messages[messageKey] || messages.unavailable;
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

readSummaryButton.addEventListener("click", () => {
  readCurrentTabSummary().catch(() => setStatus("unavailable"));
});
