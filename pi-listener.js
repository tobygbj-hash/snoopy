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

  const scheduleBase = "http://127.0.0.1:8766";

  window.SNOOPY_PI_SCHEDULER = {
    async handleVoiceCommand(transcript) {
      const response = await fetch(`${scheduleBase}/v1/voice-command`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transcript }),
      });

      if (!response.ok) {
        throw new Error("Scheduling bridge voice command failed.");
      }

      return response.json();
    },

    async fetchSchedule() {
      const response = await fetch(`${scheduleBase}/v1/schedule`);

      if (!response.ok) {
        throw new Error("Scheduling bridge read failed.");
      }

      return response.json();
    },

    async updateCalendarConfig(config) {
      const response = await fetch(`${scheduleBase}/v1/calendar/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        throw new Error("Calendar config update failed.");
      }

      return response.json();
    },

    async pollPendingSpeech(onSpeak) {
      const response = await fetch(`${scheduleBase}/v1/pending-speech`);

      if (!response.ok) {
        return;
      }

      const payload = await response.json();
      const pending = payload.pending || [];

      for (const item of pending) {
        if (typeof onSpeak === "function") {
          onSpeak(item);
        }

        await fetch(`${scheduleBase}/v1/pending-speech/ack`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ id: item.id }),
        });
      }
    },
  };
})();
