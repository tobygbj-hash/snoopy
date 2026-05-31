"use strict";

(() => {
  if (window.__snoopySummaryReaderInstalled) {
    return;
  }

  window.__snoopySummaryReaderInstalled = true;

  const speechLines = {
    intro: "Toby, here is the short summary.",
    noSummary:
      "Toby, I could not find a Google AI summary on this page yet. Please open a Google results page with an AI summary and try again.",
    reading: "Reading the Google AI summary for Toby.",
    unsupported:
      "Toby, this browser cannot read the summary aloud from this page.",
  };

  const blockedWordCodes = [
    [97, 115, 115, 104, 111, 108, 101],
    [98, 97, 115, 116, 97, 114, 100],
    [98, 105, 116, 99, 104],
    [99, 117, 110, 116],
    [100, 97, 109, 110],
    [100, 105, 99, 107],
    [102, 117, 99, 107],
    [104, 101, 108, 108],
    [112, 105, 115, 115],
    [115, 104, 105, 116],
  ];

  const blockedSpeechWords = blockedWordCodes.map((codes) =>
    String.fromCharCode(...codes),
  );

  let statusElement = null;

  function installButton() {
    if (!isSupportedGoogleResultsPage()) {
      return;
    }

    if (document.querySelector(".snoopy-summary-reader-button")) {
      return;
    }

    const button = document.createElement("button");
    button.type = "button";
    button.className = "snoopy-summary-reader-button";
    button.textContent = "Read AI summary";
    button.addEventListener("click", () => {
      readSummaryAloud();
    });

    document.body.append(button);
  }

  function isSupportedGoogleResultsPage() {
    return location.hostname === "www.google.com" && location.pathname === "/search";
  }

  function readSummaryAloud() {
    const summary = findGoogleAiSummary();

    if (!summary) {
      showStatus(speechLines.noSummary);
      speak(speechLines.noSummary);
      return { ok: false, message: speechLines.noSummary };
    }

    const safeSummary = prepareSpeechText(summary);
    const spokenText = `${speechLines.intro} ${safeSummary}`;

    showStatus(speechLines.reading);
    speak(spokenText);

    return { ok: true, message: speechLines.reading };
  }

  function findGoogleAiSummary() {
    const marker = findAiSummaryMarker();

    if (!marker) {
      return "";
    }

    const container = findSummaryContainer(marker);
    const text = cleanSummaryText(container ? container.innerText : marker.parentElement?.innerText);

    return shortenSummary(text);
  }

  function findAiSummaryMarker() {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        const text = normalizeText(node.textContent);

        if (/^(AI Overview|AI Mode)$/i.test(text) || /^AI Overview\b/i.test(text)) {
          return NodeFilter.FILTER_ACCEPT;
        }

        return NodeFilter.FILTER_SKIP;
      },
    });

    return walker.nextNode()?.parentElement || null;
  }

  function findSummaryContainer(marker) {
    let current = marker;
    let best = marker;

    for (let depth = 0; current && depth < 8; depth += 1) {
      const text = cleanSummaryText(current.innerText);

      if (text.length > 160 && text.length < 5000) {
        best = current;
      }

      if (current.matches?.("body")) {
        break;
      }

      current = current.parentElement;
    }

    return best;
  }

  function cleanSummaryText(text = "") {
    const lines = normalizeText(text)
      .split(/\n+/)
      .map((line) => line.trim())
      .filter(Boolean)
      .filter((line) => !/^(AI Overview|AI Mode|Show more|Show less|Sources?|Listen|Share)$/i.test(line))
      .filter((line) => !/^\d+$/.test(line))
      .filter((line) => !/^https?:\/\//i.test(line));

    return lines.join(" ").replace(/\s+/g, " ").trim();
  }

  function shortenSummary(text) {
    const cleaned = text.replace(/^AI Overview\s*/i, "").replace(/^AI Mode\s*/i, "").trim();

    if (cleaned.length <= 900) {
      return cleaned;
    }

    const sentenceBoundary = cleaned.slice(0, 900).lastIndexOf(".");

    if (sentenceBoundary > 300) {
      return cleaned.slice(0, sentenceBoundary + 1);
    }

    return `${cleaned.slice(0, 897).trim()}...`;
  }

  function prepareSpeechText(text) {
    return neutralizeUnsafeSpeech(text)
      .replace(/[^\S\r\n]+/g, " ")
      .replace(/\s+([.,;:!?])/g, "$1")
      .trim();
  }

  function neutralizeUnsafeSpeech(text) {
    return blockedSpeechWords.reduce((safeText, word) => {
      const pattern = new RegExp(`\\b${escapeRegExp(word)}\\b`, "gi");
      return safeText.replace(pattern, "gentle word");
    }, text);
  }

  function speak(text) {
    if (!("speechSynthesis" in window) || !("SpeechSynthesisUtterance" in window)) {
      showStatus(speechLines.unsupported);
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

  function showStatus(message) {
    if (!statusElement) {
      statusElement = document.createElement("div");
      statusElement.className = "snoopy-summary-reader-status";
      statusElement.setAttribute("role", "status");
      document.body.append(statusElement);
    }

    statusElement.textContent = message;
    window.setTimeout(() => {
      if (statusElement) {
        statusElement.remove();
        statusElement = null;
      }
    }, 4000);
  }

  function normalizeText(text = "") {
    return text.replace(/[\u200B-\u200D\uFEFF]/g, "").replace(/\s+/g, " ").trim();
  }

  function escapeRegExp(text) {
    return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message?.type !== "SNOOPY_READ_GOOGLE_AI_SUMMARY") {
      return false;
    }

    sendResponse(readSummaryAloud());
    return false;
  });

  installButton();
})();
