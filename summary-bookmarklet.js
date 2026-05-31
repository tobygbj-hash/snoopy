"use strict";

const bookmarkletLink = document.querySelector("#bookmarkletLink");
const bookmarkletStatus = document.querySelector("#bookmarkletStatus");

const bookmarkletSource = `(() => {
  const speechLines = {
    intro: "Toby, here is the short summary.",
    noSummary: "Toby, I could not find a Google AI summary on this page yet.",
    wrongPage: "Toby, please use this on a Google results page.",
    unsupported: "Toby, this browser cannot read the summary aloud from this page."
  };
  const blockedWordCodes = [
    [97,115,115,104,111,108,101],
    [98,97,115,116,97,114,100],
    [98,105,116,99,104],
    [99,117,110,116],
    [100,97,109,110],
    [100,105,99,107],
    [102,117,99,107],
    [104,101,108,108],
    [112,105,115,115],
    [115,104,105,116]
  ];
  const blockedSpeechWords = blockedWordCodes.map((codes) => String.fromCharCode(...codes));

  function readSummary() {
    if (location.hostname !== "www.google.com" || location.pathname !== "/search") {
      speak(speechLines.wrongPage);
      return;
    }

    const summary = findGoogleAiSummary();

    if (!summary) {
      speak(speechLines.noSummary);
      return;
    }

    speak(speechLines.intro + " " + prepareSpeechText(summary));
  }

  function findGoogleAiSummary() {
    const marker = findAiSummaryMarker();

    if (!marker) {
      return "";
    }

    const container = findSummaryContainer(marker);
    const text = cleanSummaryText(container ? container.innerText : marker.parentElement && marker.parentElement.innerText);

    return shortenSummary(text);
  }

  function findAiSummaryMarker() {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        const text = normalizeText(node.textContent);

        if (/^(AI Overview|AI Mode)$/i.test(text) || /^AI Overview\\b/i.test(text)) {
          return NodeFilter.FILTER_ACCEPT;
        }

        return NodeFilter.FILTER_SKIP;
      }
    });

    const node = walker.nextNode();
    return node ? node.parentElement : null;
  }

  function findSummaryContainer(marker) {
    let current = marker;
    let best = marker;

    for (let depth = 0; current && depth < 8; depth += 1) {
      const text = cleanSummaryText(current.innerText);

      if (text.length > 160 && text.length < 5000) {
        best = current;
      }

      if (current.matches && current.matches("body")) {
        break;
      }

      current = current.parentElement;
    }

    return best;
  }

  function cleanSummaryText(text = "") {
    const lines = normalizeText(text)
      .split(/\\n+/)
      .map((line) => line.trim())
      .filter(Boolean)
      .filter((line) => !/^(AI Overview|AI Mode|Show more|Show less|Sources?|Listen|Share)$/i.test(line))
      .filter((line) => !/^\\d+$/.test(line))
      .filter((line) => !/^https?:\\/\\//i.test(line));

    return lines.join(" ").replace(/\\s+/g, " ").trim();
  }

  function shortenSummary(text) {
    const cleaned = text.replace(/^AI Overview\\s*/i, "").replace(/^AI Mode\\s*/i, "").trim();

    if (cleaned.length <= 900) {
      return cleaned;
    }

    const sentenceBoundary = cleaned.slice(0, 900).lastIndexOf(".");

    if (sentenceBoundary > 300) {
      return cleaned.slice(0, sentenceBoundary + 1);
    }

    return cleaned.slice(0, 897).trim() + "...";
  }

  function prepareSpeechText(text) {
    return neutralizeUnsafeSpeech(text)
      .replace(/[^\\S\\r\\n]+/g, " ")
      .replace(/\\s+([.,;:!?])/g, "$1")
      .trim();
  }

  function neutralizeUnsafeSpeech(text) {
    return blockedSpeechWords.reduce((safeText, word) => {
      const pattern = new RegExp("\\\\b" + escapeRegExp(word) + "\\\\b", "gi");
      return safeText.replace(pattern, "gentle word");
    }, text);
  }

  function speak(text) {
    if (!("speechSynthesis" in window) || !("SpeechSynthesisUtterance" in window)) {
      alert(speechLines.unsupported);
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

  function normalizeText(text = "") {
    return text.replace(/[\\u200B-\\u200D\\uFEFF]/g, "").replace(/\\s+/g, " ").trim();
  }

  function escapeRegExp(text) {
    return text.replace(/[.*+?^$\\{\\}()|[\\]\\\\]/g, "\\\\$&");
  }

  readSummary();
})();`;

bookmarkletLink.href = `javascript:${encodeURIComponent(bookmarkletSource)}`;
bookmarkletStatus.textContent =
  "Ready, Toby. Drag the orange button to your bookmarks bar.";
