"use strict";

// Raspberry Pi only: talks to the local speaker-id bridge (see pi/speaker-id/).
(function setupPiListener() {
  const params = new URLSearchParams(window.location.search);
  const piMode = params.get("pi") === "1" || params.get("pi") === "true";

  if (!piMode) {
    return;
  }

  const bridgeBase = "http://127.0.0.1:8765";

  window.SNOOPY_PI_LISTENER = {
    async loadCatalog() {
      const response = await fetch(`${bridgeBase}/v1/catalog`);

      if (!response.ok) {
        throw new Error("Speaker bridge catalog failed.");
      }

      window.SNOOPY_SPEAKER_CATALOG = await response.json();
    },

    async identifyActiveSpeaker() {
      const response = await fetch(`${bridgeBase}/v1/identify-now`, {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error("Speaker bridge identify failed.");
      }

      return response.json();
    },

    async fetchActiveSpeaker() {
      const response = await fetch(`${bridgeBase}/v1/active-speaker`);

      if (!response.ok) {
        throw new Error("Speaker bridge read failed.");
      }

      return response.json();
    },
  };
})();
