"use strict";

const bookmarkletLink = document.querySelector("#bookmarkletLink");
const bookmarkletStatus = document.querySelector("#bookmarkletStatus");

const bookmarkletSource = `(() => {
  const speechLines = {
    intro: "Toby, here is the short summary.",
    noSummary: "Toby, I could not find a Google AI summary on this page yet.",
    wrongPage: "Toby, please use this on a Google results page.",
    stopped: "Of course, Toby. I have stopped reading for you.",
    stopReady: "Sure, Toby. Say stop whenever you want me to pause.",
    unsupported: "Toby, this browser cannot read the summary aloud from this page."
  };
  const wakeWords = [
    "wake up snoopy",
    "attention snoopy",
    "hello snoopy",
    "hey snoopy",
    "hi snoopy",
    "okay snoopy",
    "ok snoopy",
    "yo snoopy"
  ];
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
  const stopCommands = ["stop", "stop reading", "please stop", "snoopy stop", "stop listening"];
  let stopRecognition = null;
  let isReadingAloud = false;
  let armedForStop = false;

  function normalizeCommand(transcript) {
    return transcript.trim().toLowerCase().replace(/[.,!?;:]+$/g, "").replace(/\s+/g, " ");
  }

  function remainderAfterWakeWords(transcript) {
    let remainder = normalizeCommand(transcript);

    for (const phrase of wakeWords) {
      if (remainder === phrase) {
        return "";
      }

      const prefix = phrase + " ";

      if (remainder.startsWith(prefix)) {
        remainder = remainder.slice(prefix.length).trim();
      }
    }

    return remainder;
  }

  function isStopCommand(transcript) {
    const normalized = normalizeCommand(transcript);
    const afterWake = remainderAfterWakeWords(transcript);
    return stopCommands.includes(normalized) || stopCommands.includes(afterWake);
  }

  function isWakePhraseOnly(transcript) {
    return wakeWords.includes(normalizeCommand(transcript));
  }

  function handleStopWhileReading() {
    armedForStop = false;
    cancelReading();
    speak(speechLines.stopped, false);
  }

  function stopStopListener() {
    if (!stopRecognition) {
      return;
    }

    const recognition = stopRecognition;
    stopRecognition = null;
    recognition.onend = null;

    try {
      recognition.stop();
    } catch (error) {}
  }

  function cancelReading() {
    window.speechSynthesis.cancel();
    isReadingAloud = false;
    stopStopListener();
  }

  function startStopListener() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition || null;

    if (!SpeechRecognition) {
      return;
    }

    stopStopListener();
    stopRecognition = new SpeechRecognition();
    stopRecognition.continuous = true;
    stopRecognition.interimResults = false;
    stopRecognition.lang = "en-US";

    stopRecognition.onresult = (event) => {
      const latestResult = event.results[event.results.length - 1];

      if (!latestResult.isFinal || !isReadingAloud) {
        return;
      }

      const transcript = latestResult[0].transcript;

      if (isWakePhraseOnly(transcript)) {
        armedForStop = true;
        return;
      }

      if (isStopCommand(transcript)) {
        handleStopWhileReading();
      }
    };

    stopRecognition.onend = () => {
      if (!isReadingAloud || !stopRecognition) {
        return;
      }

      try {
        stopRecognition.start();
      } catch (error) {
        stopStopListener();
      }
    };

    stopRecognition.onerror = () => {
      if (isReadingAloud) {
        stopStopListener();
      }
    };

    try {
      stopRecognition.start();
    } catch (error) {
      stopRecognition = null;
    }
  }

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

    speak(speechLines.intro + " " + prepareSpeechText(summary), true);
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

  function speak(text, listenForStop) {
    if (!("speechSynthesis" in window) || !("SpeechSynthesisUtterance" in window)) {
      alert(speechLines.unsupported);
      return;
    }

    if (listenForStop) {
      armedForStop = false;
      cancelReading();
    } else {
      window.speechSynthesis.cancel();
      isReadingAloud = false;
      stopStopListener();
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-US";
    utterance.pitch = 1.12;
    utterance.rate = 0.96;
    utterance.volume = 0.9;

    utterance.onend = () => {
      if (listenForStop) {
        isReadingAloud = false;
        stopStopListener();
      }
    };

    utterance.onerror = () => {
      if (listenForStop) {
        isReadingAloud = false;
        stopStopListener();
      }
    };

    if (listenForStop) {
      isReadingAloud = true;
      startStopListener();
    }

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
