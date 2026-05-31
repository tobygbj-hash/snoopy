## Summary

<!-- What changed and why -->

## How to test

<!-- Steps Toby or a maintainer can follow -->

- [ ] `npm test` passes locally
- [ ] Voice agent tested in Chrome or Edge (if `app.js` / `index.html` changed)
- [ ] Extension or bookmarklet tested on a Google AI summary page (if applicable)

## Privacy checklist

- [ ] No `fetch`, storage, cookies, or telemetry added to browser code
- [ ] New spoken lines use `speechLines` and include "Toby"
- [ ] CSP unchanged or tightened (not weakened) on static HTML pages
- [ ] Extension `host_permissions` unchanged unless intentionally documented

## Docs

- [ ] README or `docs/` updated if behavior or operations changed
- [ ] CHANGELOG.md updated for user-visible changes
