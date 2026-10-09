# Security

This is a pilot release. Use HTTPS with a certificate trusted by managed clients. Do not expose the internal API directly or enable development HTTP outside loopback. Choose unique administrator and remote access passwords.

Do not post credentials, enrollment tokens, private keys, database files, `.env`, backups, private client builds or real device logs in public issues. To report a vulnerability, use GitHub's **Security → Report a vulnerability** if available; otherwise contact the repository owner privately through an established channel before disclosing exploit details. Ordinary non-sensitive bugs may use Issues.

Administrator passwords use Argon2, sessions are HttpOnly/Secure with CSRF checks, and device policy/update manifests use Ed25519 signatures. Signing does not encrypt policy contents; HTTPS is required. The server and its signing key are trusted management authorities. A compromised server/root account can control managed policy. Protect backups accordingly.

The current pilot is the supported release line. Security fixes will be documented in release notes; no response-time guarantee is offered. Dependencies are pinned for repeatable application builds, but OS repositories and base image tags remain upstream dependencies. Container image signing, a third-party penetration test, MFA and tamper-proof external audit storage are not provided.
