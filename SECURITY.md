# Security policy

## Supported versions

Security fixes target the latest published tag. Older versions may receive
best-effort guidance, but users should upgrade to the latest tag before
reporting behavior that may already be corrected. An untagged branch or pull
request is a candidate, not a supported release.

## Reporting

GitHub private vulnerability reporting is not enabled for this repository.
Do not put exploit details, credentials, private repository content, or other
sensitive information in a public issue.

For a sensitive report, use a contact route publicly listed on
[the maintainer's GitHub profile](https://github.com/scottconverse) and provide
the affected version, impact, and a minimal reproduction through that private
route. If no suitable private route is listed, disclose only that you need a
private security contact; do not publish the sensitive details.

Non-sensitive bugs and hardening suggestions may use the
[repository issue tracker](https://github.com/scottconverse/dev-rigor-stack-lite/issues).

## Security model

dev-rigor-stack-lite is a local, text-first workflow bundle. It does not install
a service, background runtime, lifecycle hooks, or a private evidence store. Its
security boundaries are therefore deliberately narrow:

- The installers run with the invoking user's filesystem permissions. Review
  and pin the source before running them.
- Target, goals, and anchor paths are trusted operator input. Explicit
  `-Goals`/`--goals` and `-Anchor`/`--anchor` values override inference.
- `-Force`/`--force` is destructive within its documented scope: it replaces
  each of the 19 manifest-named skill directories and overwrites the installed
  `rigor_goals.py`. Back up local modifications before using it.
- Anchor management trusts its marker pair. The installer replaces the span
  between the dev-rigor-lite markers and preserves text outside it. A missing
  end marker is a hard stop; duplicate or hand-edited markers require manual
  review.
- Host policy, not this bundle, controls agent permissions, approvals,
  delegation, network access, merges, and publication.
- Workflow instructions can improve discipline but cannot mechanically prevent
  a capable process from ignoring or modifying local files.

## Sensitive data

Do not record secrets, tokens, credentials, private customer data, or
confidential source excerpts in `./.rigor/`, verification logs, screenshots,
run manifests, or review artifacts. Evidence is often copied into CI artifacts
or pull requests and should be treated as potentially public.

`./.rigor/` contains ordinary `goals.json` and `ledger.jsonl` files. It is not
encrypted, access-controlled, remotely backed up, or tamper-evident. A process
with worktree write access can change or delete it. Preserve important project
state in an appropriately protected project system of record.

See the [architecture boundaries](docs/architecture.md) and the
[safe lifecycle procedures](docs/manual.md) for additional operational detail.
