# Changelog

## 1.0.0-pilot.1

First independent public panel release.

- Publish the existing English/Persian management panel, policy catalog, API tests and Windows registration helper.
- Add a public, tagged installer without private GitHub authentication.
- Add shared-server Docker deployment modes: automatic HTTPS with selectable port, or loopback-only backend for an existing host reverse proxy.
- Check occupied ports and reuse existing Docker; install missing prerequisites without removing conflicting packages or stopping unrelated services.
- Add restart/resume, consistent data backup, English/Persian guides, license/attribution and CI.

Regression surface: panel Python modules, UI assets and client enrollment protocol are copied unchanged from the parent project. The new deployment behavior lives in `install.sh`, `scripts/install-lib.sh`, `manage.sh`, `compose*.yaml` and `Caddyfile`. The private client repository and installed Windows service are untouched. See OPERATIONS.md for pilot acceptance limits.
