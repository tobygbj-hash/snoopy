"use strict";

// Speaker catalog (static file — no network fetch). Profiles are matched on the Pi
// by local voice enrollment; the browser only needs display names.
window.SNOOPY_SPEAKER_CATALOG = {
  defaultProfileId: "toby",
  guestProfileId: "guest",
  profiles: {
    toby: {
      displayName: "Toby",
    },
    guest: {
      displayName: "friend",
    },
  },
};
