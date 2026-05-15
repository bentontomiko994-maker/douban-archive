# CLAUDE.md — Douban Archive Codebase Guide

This file orients AI assistants working on the Douban Archive project.

---

## Project Overview

**Douban Archive** is a local-first Chromium browser extension (Manifest V3) that lets users export their own Douban book, movie, and music collection data into local files (JSON, Excel CSV, Markdown). It runs entirely in the browser using the user's existing login session — no server, no third-party accounts, no data uploads.

Current version: **v0.3.1** (MVP)

---

## Repository Structure

```
douban-archive/
├── extension/              # All browser extension source code
│   ├── manifest.json       # MV3 manifest — permissions, host rules, entry points
│   ├── background.js       # Service worker: export logic, parsing, file generation
│   ├── popup.html          # Extension popup UI markup
│   ├── popup.js            # Popup UI logic, communicates with background via messages
│   └── popup.css           # Popup styles (CSS custom properties, green theme)
├── docs/
│   ├── en/                 # English documentation
│   │   ├── PROJECT_SPEC.md
│   │   ├── USER_GUIDE.md
│   │   ├── RISK_AND_RELEASE_GUIDE.md
│   │   └── RELEASE_NOTES_v0.3.1.md
│   └── zh-CN/              # Simplified Chinese documentation (mirrors en/)
│       ├── PROJECT_SPEC.md
│       ├── USER_GUIDE.md
│       ├── RISK_AND_RELEASE_GUIDE.md
│       ├── RELEASE_NOTES_v0.3.1.md
│       ├── OBSIDIAN_COPY.md
│       └── SOCIAL_COPY.md
├── README.md               # Chinese-first README
├── README.zh-CN.md         # English README
├── CHANGELOG.md
├── PRIVACY.md
├── SECURITY.md
└── .gitignore
```

No build system, bundler, or package manager — the extension runs directly from source files loaded in developer mode.

---

## Architecture

### Communication Pattern (Manifest V3)

The extension uses the standard MV3 message-passing pattern:

```
popup.js  ──sendMessage──►  background.js (service worker)
          ◄──sendResponse──
```

Three message types:

| `message.type`   | Direction         | Purpose                                    |
|------------------|-------------------|--------------------------------------------|
| `START_EXPORT`   | popup → background | Begin export with `payload` (options)     |
| `STOP_EXPORT`    | popup → background | Request graceful stop                      |
| `GET_STATUS`     | popup → background | Poll current `state` snapshot              |

The popup polls every **1200 ms** (`setInterval`) and updates the progress bar, status text, and log.

### Export Flow (`background.js`)

```
runExport(options)
  └── for each selected scope:
        exportScope(userId, scope, delayMs, includeDetails)
          └── loop pages:
                fetchText(url)          ← fetch with credentials: "include"
                parsePage(html, scope)  ← regex-based HTML parsing
                  ├── parseCollectionPage()  (books/movies/music)
                  ├── parseStatuses()
                  ├── parseNotes()
                  └── parseReviews()
                [optional] fetchDetail(item.url) ← detail page fetch
  └── buildFile(archive, format)        ← JSON / CSV / Markdown
  └── downloadFile()                    ← chrome.downloads.download()
```

State is held in a module-level `state` object (not `chrome.storage`) because the service worker lifetime is sufficient for a single export session.

---

## Key Concepts

### Scopes

A **scope** defines a single export unit. Both `background.js` and `popup.js` define a `SCOPES` array (they are separate contexts and cannot share modules in MV3).

`background.js` scope shape (full):
```js
{ key, domain, label, type, status, kind }
// kind: "collection" | "statuses" | "notes" | "reviews"
```

`popup.js` scope shape (display-only):
```js
{ key, label, type }
// type used for filter buttons: "book" | "movie" | "music" | "writing" | "review"
```

Scope keys:
- `book-collect`, `book-wish`, `book-do`
- `movie-collect`, `movie-wish`, `movie-do`
- `music-collect`, `music-wish`, `music-do`
- `statuses`, `notes`, `reviews`

### Pagination

- Collections: `start` parameter increments by `PAGE_SIZE = 15` per page; `page` counter also increments for statuses.
- Notes and reviews: `start` parameter only.
- Stop condition: `hasNextPage(html)` — looks for a `.next` CSS class or `rel="next"` link.

### Detail Fetching

- **Always fetched**: notes (`kind === "notes"`) and reviews (`kind === "reviews"`).
- **User-optional**: collection items when `includeDetails` checkbox is checked.
- Detail is attached as `item.detail` with `title`, `content`/`summary`, `publishedAt`, `url`, `fetchedAt`.

### Rating Normalization

`parseRating(block)` extracts ratings from three patterns (in priority order):
1. CSS class `allstarN` (N = 10, 20, 30, 40, 50)
2. CSS class `ratingN-t`
3. Text pattern `N星`

All values are normalized to a 1–5 scale via `normalizeRatingNumber()`. Stored fields:
- `ratingValue` — numeric 1–5 or `null`
- `ratingMax` — always `5` when rated, else `null`
- `ratingPercent` — `ratingValue / 5` when rated, else `null`

### Block Parsing Strategy

No DOM parser is used (service worker context). All HTML parsing is regex-based:
- `splitBlocks(html, startPattern, endTag)` — splits HTML into item blocks
- `firstMatch(text, pattern)` — returns first capture group or `""`
- `cleanText(text)` — strips tags → decodes HTML entities → collapses whitespace
- `sliceAround(text, index, radius)` — context window around a match for surrounding-block extraction

### Block Detection Fallback

`parseCollectionPage` tries `<li class="subject-item|item">` first, then falls back to `<div class="item">` if no blocks found. This makes parsing resilient across Douban's varying page structures.

---

## Output Formats

### JSON (default, recommended)

Full `archive` object:
```json
{
  "meta": {
    "tool": "Douban Archive",
    "version": "0.3.1",
    "userId": "...",
    "exportedAt": "ISO8601",
    "formatVersion": 1,
    "privacy": "local-only"
  },
  "items": [ ...ItemObjects ],
  "errors": [ { "scope", "url"/"page", "message" } ]
}
```

### CSV

- UTF-8 BOM prefix (`﻿`) + CRLF line endings → fixes Chinese mojibake in Excel.
- Columns: `id`, `type`, `status`, `statusLabel`, `title`, `url`, `ratingValue`, `ratingMax`, `ratingPercent`, `comment`, `content`, `detailContent`, `tags`, `collectedAt`, `publishedAt`.
- Arrays (e.g. `tags`) are joined with spaces.

### Markdown

- H1: archive header with user ID and export timestamp.
- H2 per item: title or status label.
- List items: type, status, rating, date, URL, tags.
- Body paragraph: `comment`, `content`, `detail.content`, or `excerpt` (first non-empty).

---

## Item Data Model

All items share a common base; scope-specific fields are additive.

**Collection items** (books, movies, music):
```
id, type, status, statusLabel, title, url, cover,
rating, ratingValue, ratingMax, ratingPercent,
comment, shortReview, tags, collectedAt,
sourceUrl, exportedAt,
[detail?: { title, summary, fetchedAt }]
```

**Status items** (broadcasts):
```
id, type, status, statusLabel, title, url,
content, publishedAt, sourceUrl, exportedAt
```

**Note items** (diary):
```
id, type, status, statusLabel, title, url,
sourceUrl, exportedAt,
[detail: { title, content, publishedAt, url, fetchedAt }]
```

**Review items** (long reviews):
```
id, type, status, statusLabel, title, url,
rating, ratingValue, ratingMax, ratingPercent,
excerpt, publishedAt, sourceUrl, exportedAt,
[detail: { title, content, rating*, publishedAt, url, fetchedAt }]
```

---

## Extension Permissions

Declared in `manifest.json`:
- `"downloads"` — trigger file save dialog via `chrome.downloads.download()`
- `"storage"` — persist `doubanUserId` and `delayMs` across sessions via `chrome.storage.local`

Host permissions (required for `fetch` with `credentials: "include"`):
- `https://book.douban.com/*`
- `https://movie.douban.com/*`
- `https://music.douban.com/*`
- `https://www.douban.com/*`

---

## UI Conventions (`popup.html` / `popup.css`)

- **Width**: 420px fixed; min-height 560px.
- **Color palette**: CSS custom properties prefixed with `--`. Main accent is `--green: #2f8f5b`.
- **Scope grid**: 3-column CSS grid; selection state driven by `:has(input:checked)` — no JS class toggling.
- **Button variants**: `.primary` (green fill), `.secondary` (mint fill, fixed width), `.ghost` (mint fill, compact).
- **No framework**: vanilla HTML/CSS/JS only. Do not introduce React, Vue, or other frameworks.

---

## Development Conventions

### No Build Step

Load the `extension/` folder directly in Chrome via `chrome://extensions` → developer mode → "Load unpacked". After editing any file, click the reload button on the extensions page (or use a keyboard shortcut).

### No External Dependencies

The project intentionally has zero npm dependencies, no bundler, and no transpilation. Keep it that way unless there is a strong reason to change. Use standard browser APIs and vanilla JS.

### Coding Style

- **ES2020+ features** are fine: optional chaining (`?.`), nullish coalescing (`??`), `Array.from`, `matchAll`, template literals.
- **No classes**: the codebase uses module-scope state and plain functions.
- **No comments on obvious logic**: add a comment only when the why is non-obvious (e.g., the UTF-8 BOM rationale, why a regex fallback exists).
- **String parsing over DOM**: the service worker has no `document`; use `firstMatch`, `splitBlocks`, `cleanText` helpers.
- **`const` by default**, `let` for loop variables that reassign.
- Function names are camelCase; scope keys are kebab-case.

### Adding a New Scope

1. Add entry to `SCOPES` array in **both** `background.js` and `popup.js`.
2. If a new `kind`, implement a `parseFoo(html, scope, sourceUrl)` function and a `parseFooDetail(html, url)` function, then wire them into `parsePage` and `fetchDetail`.
3. Add the new `kind` to `buildScopeUrl`.
4. Update the scope filter buttons in `popup.html` if the `type` grouping changes.
5. Update `README.md`, `CHANGELOG.md`, and bilingual docs.

### Delaying Requests

The minimum configurable delay is **1200 ms** (enforced in `popup.js: startExport`). Default is **2200 ms**. Never remove this lower bound — it reduces the risk of rate-limiting and is part of the project's responsible-use stance.

### Error Handling

- Per-page and per-item errors are pushed to `state.archive.errors` and do not abort the export.
- Only throw inside `runExport` for fatal conditions (e.g., zero items exported with errors present).
- Block-detection failures return an empty array; the export continues to the next page.

---

## Compliance and Ethical Boundaries

These are non-negotiable constraints — do not write code that crosses them:

- Export only data accessible in the user's own logged-in session.
- Do not bypass CAPTCHA, login walls, paywalls, or access controls.
- Do not collect other users' private content.
- Do not upload any data to external servers.
- Do not add analytics, telemetry, or any form of remote reporting.
- The extension must work entirely offline after the page HTML is fetched.

The `looksBlocked(html)` check detects Douban's challenge pages and surfaces a human-readable error instead of silently parsing garbage.

---

## What NOT to Commit

- `.pem` extension signing keys
- `.crx` packaged extension files
- Real exported Douban archive files (even anonymized samples need care)
- Screenshots containing private user data
- Browser cookies, tokens, or passwords
- Debug logs with user IDs or personal data

---

## Roadmap Context

When implementing future features, keep these planned directions in mind:

- Incremental / resume-from-checkpoint export
- Group posts and comments (deferred — complex, higher risk)
- Local archive index for browsing exported data
- AI-readable interest profile generation from exports
- Automated tests using saved HTML samples (no live network calls)
- Bilingual project website

---

## Testing

There is currently no automated test suite. Manual testing is done by:

1. Loading the extension in a Chromium browser in developer mode.
2. Logging into Douban with a real account.
3. Running exports against each scope and verifying output files.

When adding tests in the future, use saved HTML samples as fixtures so tests never make live network requests.

---

## Documentation Conventions

All user-facing docs are maintained in bilingual pairs:

| English                                | Chinese (Simplified)                        |
|----------------------------------------|---------------------------------------------|
| `README.zh-CN.md` (project root)       | `README.md` (project root)                  |
| `docs/en/USER_GUIDE.md`                | `docs/zh-CN/USER_GUIDE.md`                  |
| `docs/en/RISK_AND_RELEASE_GUIDE.md`    | `docs/zh-CN/RISK_AND_RELEASE_GUIDE.md`      |
| `docs/en/PROJECT_SPEC.md`              | `docs/zh-CN/PROJECT_SPEC.md`                |

When you add a new feature or fix, update **both** the English and Chinese versions. The Chinese README (`README.md`) is the primary/first file; the English README is `README.zh-CN.md` (historical naming — do not rename).
