# Commit conventions

Consistent commits make history easy to scan and help automated agents pick up
context quickly.

## Message format

Use [Conventional Commits](https://www.conventionalcommits.org/) style:

```
<type>(<optional scope>): <short summary>

<optional body — what and why, not implementation diary>
```

### Types

| Type | When to use |
| ---- | ----------- |
| `feat` | New behavior for Toby (voice, extension, bookmarklet) |
| `fix` | Bug fix |
| `docs` | README, docs/, comments only |
| `chore` | Tooling, CI, dependencies, repo hygiene |
| `test` | Tests or policy checks only |
| `refactor` | Code change without behavior change |

### Scopes (optional)

`app`, `extension`, `bookmarklet`, `ci`, `docs`, `policy`

### Examples

```
feat(app): reserve search tab before listening starts

fix(extension): match updated Google AI summary container

docs: add operations guide and commit conventions

chore(ci): deploy bookmarklet files to GitHub Pages
```

## Rules

1. **Subject line:** Imperative mood, ~72 characters or less, no trailing period.
2. **Body:** Wrap at ~72 characters; explain *why* when it is not obvious.
3. **One concern per commit** when possible (docs separate from feature code).
4. **Run `npm test`** before committing changes to JS/HTML/extension files.
5. **Privacy:** Do not commit API keys, handoff JSON from a real session, or
   recordings.

## Branch names

For feature work:

```
cursor/<short-description>-0c8f
```

Use lowercase and hyphens. The `-0c8f` suffix keeps agent branches distinct on
case-insensitive filesystems.

## Git commit template

The repo includes [`.gitmessage`](../.gitmessage). Enable it once per clone:

```bash
git config commit.template .gitmessage
```

Your editor will show placeholders when you run `git commit` (without `-m`).

## Pull requests

- Target `main` unless agreed otherwise.
- Describe what changed and how Toby should verify it.
- Note if Google Pages deploy is affected (only static app files auto-deploy).
