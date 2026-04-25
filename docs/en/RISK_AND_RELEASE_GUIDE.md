# Risk and Release Guide

> This document is not legal advice. It is a practical risk-control checklist for publishing the project. For commercial or large-scale distribution, consult a qualified lawyer.

## 1. Positioning

Recommended positioning:

> Douban Archive is a local-first personal archive tool that helps users export Douban content they can already access in their own logged-in browser session.

Avoid positioning it as:

- A Douban crawler
- An anti-bot bypass tool
- A bulk scraping tool
- A platform extraction tool

## 2. Compliance Boundary

The project should follow these boundaries:

- Export only the user's own data.
- Read only pages the user can already access manually after logging in.
- Do not bypass CAPTCHA, login, permissions, paywalls, or platform restrictions.
- Do not collect private content from other users.
- Do not upload exported data to third-party servers.
- Do not publish real user exports as sample data.
- Do not use Douban trademarks in a way that implies official endorsement.

## 3. Data Rights and Platform Risk

Users often have rights and interests in their own posts, ratings, comments, notes, and personal information. They may also have rights to access or copy personal information under applicable privacy laws.

That does not mean unlimited use of a platform's systems, interfaces, page structure, brand assets, or other users' content. Platform terms may still restrict account use, system access, intellectual property, trademarks, content sharing, and abnormal access behavior.

The safest framing is:

> This tool helps users back up their own personal records. It is not designed to replace, attack, or bulk-harvest the platform.

## 4. GitHub Pre-Publish Checklist

Do not commit:

- `.pem` private key files
- `.crx` packaged extension files
- Real exported Douban archives
- Screenshots containing private information
- Cookies, tokens, or passwords
- Browser profile files
- Debug logs

Recommended files:

- `README.md`
- `README.zh-CN.md`
- `PRIVACY.md`
- `SECURITY.md`
- `LICENSE`
- `docs/zh-CN/USER_GUIDE.md`
- `docs/en/USER_GUIDE.md`
- Anonymized sample data

## 5. Private Keys, Public Keys, and Extension Packaging

Simple explanation:

- Private key: keep it secret. If someone gets it, they may impersonate your extension package.
- Public key: can be public and is used for verification.
- `.pem`: a private key file that Chrome may generate when packaging an extension. Do not upload it to GitHub.
- `.crx`: a packaged extension file. Keep it out of source control; publish it through GitHub Releases if needed.

## 6. Recommended Release Flow

1. Publish the source repository first; do not rush into Chrome Web Store.
2. Keep only source code and documentation in the repository.
3. Store `.pem` locally and never commit it.
4. Use GitHub Releases for version notes.
5. If distributing `.crx`, attach it to a release instead of committing it to source.
6. Before each release, review permissions, privacy docs, and the changelog.

## 7. Recommended Messaging

Good phrases:

- Local-first
- Personal data archive
- Data sovereignty
- Back up your digital memory
- Prepare structured data for future AI assistants

Avoid phrases:

- Crack
- Bypass anti-bot systems
- Bulk scrape
- Crawl the entire site
- Ignore restrictions

## 8. AI Usage Risks

Before sending exported data to AI tools, users should check:

- Whether the export includes private notes
- Whether it includes other people's names, contact info, or private messages
- Whether the AI service uploads or trains on the data
- Whether sensitive fields should be redacted first
- Whether local AI models are a better fit

Default recommendation:

> Use JSON as the primary backup, Markdown for reading, and Excel CSV for spreadsheet analysis. For private content, store locally first and avoid uploading blindly.

