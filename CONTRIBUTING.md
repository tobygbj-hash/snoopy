# Contributing to Snoopy

Thank you for helping improve Snoopy for Toby. This project values small, focused
changes and strict privacy boundaries.

## Getting started

1. Clone the repository and create a branch from `main`:
   `cursor/<short-description>-0c8f`
2. Read [docs/OPERATIONS.md](docs/OPERATIONS.md) to run the app locally.
3. Read [AGENTS.md](AGENTS.md) for product and privacy rules.

## Development workflow

```bash
npm test          # Required before opening a PR
npm run serve     # http://localhost:8000
```

## What we accept

- Bug fixes and UX improvements for voice search and summary reading
- Documentation and operational tooling
- Policy test updates **when** they codify an intentional rule change (explain in the PR)

## What needs extra care

- New spoken phrases: must live in `speechLines`, include "Toby", and pass policy checks
- Extension permissions or host access: must stay minimal
- Any network or storage in browser code: generally rejected

## Commits and pull requests

- Follow [docs/COMMITS.md](docs/COMMITS.md).
- Optional: `git config commit.template .gitmessage`
- Open a PR against `main` with a clear description and manual test steps for Toby.

## Changelog

User-visible changes should be noted in [CHANGELOG.md](CHANGELOG.md) under
**Unreleased** when appropriate.
