# Security Policy

## Security Principles

Douban Archive is designed around these boundaries:

- Export only data the user can already access in their own logged-in browser.
- Do not bypass login, CAPTCHA, access controls, paywalls, or platform restrictions.
- Do not collect or upload user data.
- Do not include API keys, cookies, passwords, private keys, or exported personal data in the repository.

## Secrets

Never commit secrets to GitHub. Examples include:

- Browser cookies
- API tokens
- Passwords
- Private keys
- Extension signing keys such as `.pem` files
- Real exported Douban archive files

If a secret is accidentally committed, treat it as compromised. Revoke or replace it where possible, remove it from the repository, and review the commit history.

## Reporting a Security Issue

If you find a security issue, please open a GitHub issue with minimal reproduction details and avoid including private user data.

## Publishing Checklist

Before publishing:

- Confirm `.pem`, `.crx`, exported archives, screenshots with private data, and logs are not committed.
- Review extension permissions in `extension/manifest.json`.
- Confirm the extension has no remote analytics or hidden upload behavior.
- Confirm documentation states the compliance boundary clearly.

