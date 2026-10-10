# Changelog

## 1.1.0-pilot.1

- Add explicit HTTP testing mode with IPv4/hostname and configurable port; DNS and certificates are optional.
- Preserve HTTPS as the default. Only the HTTP overlay opts out of Secure cookies; CSRF checks remain active.
- Show the configured panel URL before startup, on exit/error, and in management commands.
- Attach bootstrap input/output explicitly to the terminal and explain hidden password entry.
- Add `manage.sh configure` to change network mode while preserving accounts/data and backing up configuration.
- Publish English/Persian dashboard screenshots with demo data and document interrupted administrator setup.

Regression surface: `control/app.py` changes cookie security only for explicit HTTP opt-in. Existing HTTPS defaults remain intact. `install.sh`, `manage.sh` and `scripts/install-lib.sh` change setup prompts, URL reporting and panel-only container replacement. No native client code or remote desktop protocol changes. HTTP management enrollment is still unsupported by the Windows client.

## 1.0.0-pilot.1

First independent public panel release.

- Publish the existing English/Persian management panel, policy catalog, API tests and Windows registration helper.
- Add a public, tagged installer without private GitHub authentication.
- Add shared-server Docker deployment modes: automatic HTTPS with selectable port, or loopback-only backend for an existing host reverse proxy.
- Check occupied ports and reuse existing Docker; install missing prerequisites without removing conflicting packages or stopping unrelated services.
- Add restart/resume, consistent data backup, English/Persian guides, license/attribution and CI.

Regression surface: panel Python modules, UI assets and client enrollment protocol are copied unchanged from the parent project. The new deployment behavior lives in `install.sh`, `scripts/install-lib.sh`, `manage.sh`, `compose*.yaml` and `Caddyfile`. The private client repository and installed Windows service are untouched. See OPERATIONS.md for pilot acceptance limits.
