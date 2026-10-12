# Operator handbook — 1.2

The complete Persian walkthrough is [HANDBOOK.fa.md](HANDBOOK.fa.md). For prerequisites and proxy examples see [INSTALL](INSTALL.md); for backup restoration see [OPERATIONS](OPERATIONS.md).

## Components

The Windows client initiates HTTPS requests to the management API. hbbs/hbbr handle remote desktop rendezvous/relay separately. Merely setting an ID server, relay and hbbs public key in stock RustDesk does not enroll a device. Use a compatible managed BamdadDesk client and an organization installer.

## First enrollment

1. Install the panel and configure trusted HTTPS. HTTP/IP mode is available for isolated panel testing; the managed client requires HTTPS.
2. Upload a compatible Windows EXE under Client releases.
3. Under Enroll devices set the public management API origin, enable organization-installer registration, and save.
4. Choose release, group, expiry and maximum registrations; download the organization installer.
5. Distribute this credential-bearing installer only to authorized users. Running it with UAC installs the client service and stages its enrollment profile with restricted Windows ACLs.
6. Verify last-seen time and applied policy in Devices. The service normally checks in every 60 seconds, subject to network delays.

Disabling automatic enrollment stops new registrations from these installers; existing devices continue communicating. Manual tokens remain a separately authorized path. Revocation affects future token use, not existing devices or remote desktop access. The installer refuses to overwrite existing management enrollment; use an ordinary client EXE for updates.

## Administrators, groups and tokens

Administrator passwords require 12 characters. Form errors appear inside the dialog. Password visibility controls reveal only the value being typed, never an existing hash. Permissions and group scopes remain enforced on the API.

Tokens list expiry, remaining registrations and usage (legacy usage can be unknown). Edit label/group/remaining uses or renew from now; revoked tokens cannot be reactivated. Group deletion requires a destination for devices, removes its policy, revokes its tokens and removes that group from administrator scopes. Historical events remain.

Password source follows device, group, global, client-default precedence. Set a new password to replace it; plaintext cannot be recovered from a stored hash. Permanent + one-time enables both methods.

## Reports

Filter by Gregorian UTC dates, group, management device ID, event kind or device/peer/IP/session text. CSV includes all matches, beyond the 100-row page. `occurred` is Unix seconds. Untrusted strings are escaped against spreadsheet formula execution. These are client-reported events, not packet capture or guaranteed billing records. Duration totals use corresponding authorized/closed events; missing reports can make totals incomplete.

## Linux management

Run `sudo bash /opt/bamdaddesk-control/manage.sh` (or `sudo bamdad` on new installations). Choose status, address/ports/HTTPS, explicit-tag update with backup, backup, optional RustDesk, SSL status, or removal. Removal requires typing `DELETE PANEL DATA`; backups, Docker and the separately managed RustDesk service remain.

`manage.sh rustdesk install` asks for public host and ID/relay ports. Default TCP ports are 21115/21116/21117 and UDP 21116. Other actions: configure, status, logs, start, stop, restart, key, backup, update. Data and private keys live in `/var/lib/bamdaddesk-rustdesk`; its Compose project is independent. Updates require an explicit numeric upstream version and create a backup first. Existing unmanaged RustDesk services are not adopted or stopped. Configure client-facing server addresses/key in the panel's global policy after changing listener settings in the CLI. The web container has no Docker socket/root-command API.

Caddy issues and renews free certificates automatically in domain HTTPS mode. TCP 80 must be publicly reachable. Use existing-proxy mode for your own certificate/reverse proxy; manage its renewal there. No x-ui installation is required. `manage.sh tls` validates the public TLS endpoint without disabling certificate checks.

## API address migration

Managed client 1.7+ accepts a signed destination from its current panel and verifies the destination's signed response before persisting it. Keep the same database and signing key, make both old/new origins route to that panel, and retain the old origin until offline devices have checked in. Updating the API field does not change DNS, certificates or container ports. Older clients need an update first; an unreachable old origin needs local administrator recovery.

## Development and distribution

Install requirements.lock in Python 3.12 and run `python -m pytest -q`. NSIS (`apt-get install nsis`) enables the executable-package test; Docker includes it. The synthetic package test verifies compilation, not installation of a real Windows service. Test a real client on a disposable Windows machine before broad deployment. Client source/build instructions are in its own repository; this panel repository is not the complete RustDesk fork. Preserve AGPL notices and provide corresponding client source to recipients.

Created by **Mahdi Nosrati / مهدی نصرتی**, [email](mailto:mahdinosrati06@gmail.com), [Telegram](https://t.me/MiNosrati).
