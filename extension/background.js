"use strict";

const GOOGLE_SEARCH_URL = "https://www.google.com/search";
const SUMMARY_RETRY_COUNT = 10;
const SUMMARY_RETRY_DELAY_MS = 900;
const TAB_LOAD_TIMEOUT_MS = 12000;

const speechLines = {
  searching: "Toby, I am checking Google for that.",
  reading: "Toby, here is the short summary.",
  noSummary:
    "Toby, I could not find a Google AI summary for that search yet.",
  error: "Toby, I had trouble reading the Google AI summary.",
};

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type !== "SNOOPY_SEARCH_AND_READ_AI_OVERVIEW") {
    return false;
  }

  searchAndReadAiOverview(message.query)
    .then((response) => sendResponse(response))
    .catch(() => {
      speak(speechLines.error);
      sendResponse({ ok: false, message: speechLines.error });
    });

  return true;
});

async function searchAndReadAiOverview(rawQuery) {
  const query = normalizeQuery(rawQuery);

  if (!query) {
    speak(speechLines.error);
    return { ok: false, message: speechLines.error };
  }

  speak(speechLines.searching);

  const tab = await chrome.tabs.create({
    active: false,
    url: buildGoogleSearchUrl(query),
  });

  if (!tab.id) {
    speak(speechLines.error);
    return { ok: false, message: speechLines.error };
  }

  try {
    await waitForTabComplete(tab.id);
    await ensureContentScript(tab.id);

    const summary = await waitForSummary(tab.id);

    if (!summary) {
      speak(speechLines.noSummary);
      return { ok: false, message: speechLines.noSummary };
    }

    speak(`${speechLines.reading} ${summary}`);
    return { ok: true, message: speechLines.reading };
  } finally {
    if (tab.id) {
      await chrome.tabs.remove(tab.id).catch(() => {});
    }
  }
}

function buildGoogleSearchUrl(query) {
  const url = new URL(GOOGLE_SEARCH_URL);
  url.searchParams.set("q", query);
  return url.toString();
}

function normalizeQuery(query = "") {
  return query.replace(/\s+/g, " ").trim();
}

async function waitForTabComplete(tabId) {
  const existingTab = await chrome.tabs.get(tabId);

  if (existingTab.status === "complete") {
    return;
  }

  await new Promise((resolve) => {
    const timeoutId = setTimeout(() => {
      chrome.tabs.onUpdated.removeListener(listener);
      resolve();
    }, TAB_LOAD_TIMEOUT_MS);

    function listener(updatedTabId, changeInfo) {
      if (updatedTabId === tabId && changeInfo.status === "complete") {
        clearTimeout(timeoutId);
        chrome.tabs.onUpdated.removeListener(listener);
        resolve();
      }
    }

    chrome.tabs.onUpdated.addListener(listener);
  });
}

async function ensureContentScript(tabId) {
  try {
    await chrome.tabs.sendMessage(tabId, {
      type: "SNOOPY_PING",
    });
  } catch (error) {
    await chrome.scripting.executeScript({
      target: { tabId },
      files: ["content-script.js"],
    });
  }
}

async function waitForSummary(tabId) {
  for (let attempt = 0; attempt < SUMMARY_RETRY_COUNT; attempt += 1) {
    try {
      const response = await chrome.tabs.sendMessage(tabId, {
        type: "SNOOPY_EXTRACT_GOOGLE_AI_SUMMARY",
      });

      if (response?.ok && response.summary) {
        return response.summary;
      }
    } catch (error) {
      await ensureContentScript(tabId);
    }

    await delay(SUMMARY_RETRY_DELAY_MS);
  }

  return "";
}

function delay(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

function speak(text) {
  chrome.tts.stop();
  chrome.tts.speak(text, {
    lang: "en-US",
    pitch: 1.12,
    rate: 0.96,
    volume: 0.9,
  });
}
