# Changelog

## v0.3.1 - 2026-04-25

### Added

- Local-first Chromium extension for exporting personal Douban records.
- Book, movie, and music export scopes:
  - Books: read, wish to read, currently reading
  - Movies: watched, wish to watch, currently watching
  - Music: listened, wish to listen, currently listening
- Experimental export scopes for statuses, notes, and long reviews.
- Structured rating fields: `ratingValue`, `ratingMax`, and `ratingPercent`.
- Export formats: JSON, Excel CSV, and Markdown.
- Background export so closing the popup does not stop the task.
- Selection shortcuts: all, core, clear, books, movies, music, writing, and reviews.
- Bilingual documentation in English and Simplified Chinese.
- Privacy, security, and release-risk documentation.

### Fixed

- Added UTF-8 BOM and CRLF line endings for Excel CSV exports to prevent Chinese text mojibake when opened directly in Excel.

### Notes

- Notes and long reviews are still experimental because Douban page structures may vary by account, permission state, and page version.
- The extension does not bypass login, CAPTCHA, permissions, paywalls, or platform restrictions.

