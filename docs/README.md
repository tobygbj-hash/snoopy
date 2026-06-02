# Snoopy documentation

This folder is the home for project documentation. The root [README](../README.md)
is the quick start for Toby and family; these pages are for anyone maintaining,
deploying, or extending Snoopy.

## Guides

| Document | Purpose |
| -------- | ------- |
| [OPERATIONS.md](OPERATIONS.md) | Run locally, test, deploy to GitHub Pages, troubleshoot |
| [ARCHITECTURE.md](ARCHITECTURE.md) | How the web app, extension, and bookmarklet fit together |
| [COMMITS.md](COMMITS.md) | Commit message format and git workflow |
| [RASPBERRY-PI.md](RASPBERRY-PI.md) | Ideas for a Google Home–style device on a Pi |
| [SCHEDULING.md](SCHEDULING.md) | Pi reminders, routines, and calendar ICS sync |

## Related files at the repo root

| File | Purpose |
| ---- | ------- |
| [../AGENTS.md](../AGENTS.md) | Rules for AI coding agents working in this repo |
| [../CONTRIBUTING.md](../CONTRIBUTING.md) | How to propose changes and what CI checks |
| [../COMMITS.md](../COMMITS.md) | Short link to commit conventions (see also [COMMITS.md](COMMITS.md)) |
| [../CHANGELOG.md](../CHANGELOG.md) | Release and change history |
| [../.gitmessage](../.gitmessage) | Optional git commit message template |

## Repository layout

```
.
├── index.html, app.js, styles.css   # Voice browsing agent (GitHub Pages)
├── summary-bookmarklet.*            # No-extension AI summary reader setup
├── extension/                       # Chrome extension for Google AI summaries
├── scripts/check-agent-policy.js  # Privacy and speech-line policy tests
├── docs/                            # You are here
└── .github/workflows/pages.yml      # Deploy workflow
```

## Quick commands

```bash
npm test          # Syntax + privacy policy checks
npm run serve     # Local static server on port 8000
```
