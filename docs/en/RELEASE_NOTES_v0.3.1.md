# Douban Archive v0.3.1 Release Notes

This is the first public release candidate of Douban Archive.

Douban Archive is a local-first personal archive tool for exporting your own Douban books, movies, music, statuses, notes, and reviews to local files for long-term backup and future AI-powered interest analysis.

## Highlights

- Export books, movies, and music records
- Experimental export for statuses, notes, and long reviews
- Export ratings, tags, short comments, full text, dates, and URLs
- Export as JSON, Excel CSV, or Markdown
- Fixed Chinese mojibake when opening CSV files directly in Excel
- Background export continues after the popup closes
- Select all, core export, and category-based selection shortcuts
- Bilingual README, user guides, privacy policy, security policy, and risk guide

## Recommended Formats

- JSON: best for long-term backup and AI analysis
- Excel CSV: best for spreadsheet filtering and statistics
- Markdown: best for reading, Obsidian, and GitHub archives

## Privacy and Boundary

Douban Archive runs locally in the user's browser. It does not upload exported data, collect passwords, collect cookies, or collect tokens.

The tool is only for backing up data the user can already access after logging in. It does not bypass CAPTCHA, login, permissions, paywalls, or platform restrictions.

## Known Limitations

- Notes and long reviews are still experimental
- Douban page structures may change and require ongoing parser updates
- Resumable exports are not supported yet
- Native `.xlsx` export is not supported yet

## Next Steps

- Add `.xlsx` export
- Add resumable exports
- Add local archive preview
- Add anonymized sample data
- Add AI interest profile generation

