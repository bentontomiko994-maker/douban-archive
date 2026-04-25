# Douban Archive

A local-first browser extension for exporting your own Douban book, movie, and music collections.

Douban Archive is built for people who have spent years recording their reading, watching, listening, and cultural life on Douban, and want a private local copy of their own data.

[中文说明](README.md)

## Status

This project is currently an MVP. The first version focuses on the most stable and valuable data category: book, movie, and music collection lists. v0.3.1 fixes Chinese text mojibake when opening exported CSV files directly in Excel.

Supported:

- Export books: read, wish to read, currently reading
- Export movies: watched, wish to watch, currently watching
- Export music: listened, wish to listen, currently listening
- Experimental export: statuses and notes
- Experimental export: long reviews
- Rating export: normalized to a 1-5 star scale with `ratingValue`, `ratingMax`, and `ratingPercent`
- Short comment export from collection pages
- Full text export for notes and long reviews
- Export formats: JSON, Excel CSV, Markdown
- Optional detail-page fetch for item title and summary
- Background export: closing the popup or switching tabs does not stop the export
- Local-only execution inside your browser
- No server, no external account, no cloud upload

Not included yet:

- Group posts and comments
- Reviews and notes
- Full media image archiving
- Incremental backup and resume

## Privacy

Douban Archive runs locally in your browser. It uses your existing Douban login session to request pages that you can already access manually.

The extension does not upload your data anywhere. Exported files are downloaded directly to your computer.

More:

- [Privacy Policy](PRIVACY.md)
- [Security Policy](SECURITY.md)
- [Risk and Release Guide](docs/en/RISK_AND_RELEASE_GUIDE.md)
- [User Guide](docs/en/USER_GUIDE.md)

## Compliance Boundary

This tool is designed for personal data backup. It does not bypass login, CAPTCHA, access controls, paywalls, or platform restrictions. If Douban asks for verification, you should complete it manually in your browser and then run the export again.

The extension includes a request delay setting to reduce pressure on Douban and lower the chance of failed exports.

## Install Locally

1. Download and unzip this project, or clone the repository.
2. Find the `extension` folder.
3. Open Chrome, Edge, Arc, or another Chromium browser.
4. Go to `chrome://extensions`.
5. Enable `Developer mode`.
6. Click `Load unpacked`.
7. Select the `extension` folder.
8. Log in to Douban in the same browser.
9. Click the Douban Archive icon in the browser toolbar.

## Usage

1. Choose the export scopes.
2. Use `Select All` to export everything, or select books, movies, music, writing, and reviews by category.
3. Choose JSON, Excel CSV, or Markdown.
4. Optional: enable detail-page fetching. Notes and reviews fetch full text by default.
5. Click `Start Export`.
6. You can close the popup or switch tabs after export starts; the background task keeps running.
7. Click the extension icon again to check progress.
8. Save the generated file locally.

JSON is recommended for future AI workflows because it preserves the most structure.

## Which Format Should I Use?

- JSON: best for AI, data analysis, and future automation. It keeps structured fields such as type, status, rating, rating ratio, tags, short comments, long review content, note content, URLs, and dates. Recommended as the primary backup format.
- Markdown: best for human reading, Obsidian, personal knowledge bases, and GitHub archives. AI can read it well, but the structure is less strict than JSON.
- Excel CSV: best for spreadsheets, filtering, and statistics. Useful for ratings, tags, and dates, but less suitable for long-form text. Exported CSV files include a UTF-8 BOM so Excel should display Chinese text correctly when opened directly.

Recommendation: export JSON for serious backup, Markdown for reading, and Excel CSV for spreadsheet analysis.

## Repository Structure

```text
extension/
  manifest.json
  popup.html
  popup.css
  popup.js
docs/
  en/
  zh-CN/
README.md
README.zh-CN.md
```

## Roadmap

- Add export support for diaries
- Add export support for statuses / broadcasts
- Add export support for reviews
- Add resumable export state
- Add local archive index
- Add AI-ready profile generation
- Generate a recommendation preference summary from exported data
- Add bilingual documentation site
- Add tests with saved HTML fixtures

## AI Workflow Ideas

After exporting your data, future versions can generate:

- Interest profile
- Reading and viewing history timeline
- Recommendation seed file
- Personal knowledge graph
- Markdown archive for Obsidian
- Dataset for local AI assistants

## License

License not selected yet. If this project becomes public, MIT or AGPL can be considered depending on whether the goal is maximum reuse or stronger open-source reciprocity.
