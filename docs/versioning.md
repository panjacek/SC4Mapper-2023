# Versioning

Status: **planned** — adopt from the `v2.0.0` baseline once PR #2 merges.
`pyproject.toml` already carries `version = "2.0.0"`.

## Scheme

SemVer 2.0.0: `MAJOR.MINOR.PATCH`, single version tracked in
`pyproject.toml [project] version`. Git tags `vX.Y.Z` mark releases.

## Source of truth: conventional commits

| Commit | Bump |
|---|---|
| `fix:` | PATCH |
| `feat:` | MINOR |
| `feat!:`, `fix!:`, or commit with `BREAKING CHANGE:` footer | MAJOR |
| `chore:`, `docs:`, `ci:`, `refactor:` (no behavior change) | none |

The restructure PR is the precedent: `refactor!:` + BREAKING CHANGE footer →
the 2.0.0 major.

## Release flow (manual until automated)

1. Merge PR to `master` (squash).
2. Release commit: bump `[project] version` in `pyproject.toml`.
3. `git tag vX.Y.Z && git push origin master --tags`.
4. Optional: GitHub release with auto-generated notes from commits since the
   previous tag.

## Automation candidates (later)

- `.github/dependabot.yml`: weekly bumps for Actions versions — would have
  caught the `setup-uv` immutable-tag issue class early.
- `python-semantic-release` (or equivalent) deriving version + changelog from
  commit history; release job gated on master after CI green.
