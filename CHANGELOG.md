# Changelog

## 1.2.0

- Show form validation/errors inside administrator dialogs and add password visibility controls.
- Add token inventory, renewal, editing and revocation; legacy usage remains unknown.
- Edit groups, inspect/move members and delete with an explicit destination.
- Show inherited password source without exposing stored hashes.
- Add connection date/group/device/search filters, pagination, summaries and all-matches CSV export.
- Add configurable HTTPS management origin, an automatic-enrollment switch and downloadable NSIS organization installers.
- Expose signed API migration information for compatible client 1.7+.
- Add Linux management menu, update with backup, confirmed panel removal and TLS status.
- Add optional separately managed RustDesk OSS Docker services, port settings, key display and backup.
- Add creator attribution and detailed English/Persian operator handbooks.

Regression surface: `control/app.py` registers feature routers and extends enrollment bookkeeping; `control/storage.py` adds tables without replacing existing data. `static/app.js`, `index.html` and `style.css` change dialog feedback, password controls and feature navigation. `install.sh` adds optional server setup; `manage.sh` adds explicit operator actions. Docker adds the NSIS compiler. Existing remote desktop transport is unchanged. Native client changes are confined to management/audit URL migration in its separate repository; ordinary unmanaged operation is unchanged.

Validation: 19 local API tests and 5 native Bamdad module tests passed. Local browser verified visible administrator validation and organization controls. NSIS compilation, Docker health, RustDesk key persistence and interactive HTTP/HTTPS-proxy installation passed CI; real Windows installation and public ACME issuance are not yet acceptance-tested. Do not interpret a package-compilation test as a Windows installation test.


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
