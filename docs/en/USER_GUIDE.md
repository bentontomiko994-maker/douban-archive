# Douban Archive User Guide

Douban Archive is a local-first browser extension for exporting your own Douban books, movies, music, statuses, notes, and reviews.

## 1. Who Is It For?

Douban Archive is for people who:

- Have used Douban for years
- Want a local backup of their own Douban records
- Worry about platform changes, feature shutdowns, or account risk
- Want future AI tools to better understand their interests

## 2. Installation

1. Download and unzip the project.
2. Find the `extension` folder.
3. Open Chrome, Edge, Arc, or another Chromium browser.
4. Go to `chrome://extensions`.
5. Enable `Developer mode`.
6. Click `Load unpacked`.
7. Select the `extension` folder.
8. Log in to Douban in the same browser.
9. Click the Douban Archive icon in the browser toolbar.

## 3. Basic Usage

1. Enter your Douban user ID.
2. Choose export scopes.
3. Choose an export format.
4. Keep the default request delay unless you have a reason to change it.
5. Click `Start Export`.
6. You can close the popup or switch tabs after export starts.
7. Click the extension icon again to check progress.
8. Save the exported file locally when the export finishes.

## 4. Export Scopes

Currently supported:

- Books: read, wish to read, currently reading
- Movies: watched, wish to watch, currently watching
- Music: listened, wish to listen, currently listening
- Statuses / broadcasts
- Notes
- Long reviews

Selection shortcuts:

- `Select All`: export all supported content
- `Core`: export collected books, watched movies, and listened music
- `Clear`: deselect everything
- `Books`, `Movies`, `Music`, `Writing`, `Reviews`: choose by category

## 5. Export Formats

### JSON

Best as the primary backup format and the best format for future AI workflows.

JSON preserves structured fields such as:

- Type
- Status
- Title
- URL
- Rating
- Rating ratio
- Tags
- Short comments
- Note content
- Review content
- Dates

### Excel CSV

Best for Excel, Numbers, Google Sheets, filtering, sorting, and statistics.

The exported CSV includes a UTF-8 BOM so Excel should display Chinese text correctly when opened directly.

### Markdown

Best for human reading, Obsidian, GitHub, or personal knowledge bases.

Use Markdown when you want a readable archive.

## 6. AI Usage

If you want AI tools to understand your interests from your Douban data, JSON is the recommended format.

JSON helps AI distinguish:

- What you strongly liked
- What you disliked
- What you want to read, watch, or listen to
- Long-term topic interests
- Keywords in your comments and reviews
- How your interests changed over time

## 7. Privacy and Security

Douban Archive runs locally in your browser.

It does not:

- Upload your exported data
- Collect your password
- Collect your cookies
- Send analytics
- Share data with third parties

Exported files may include private notes, reviews, and personal interest records. Store them carefully and avoid publishing them without review.

## 8. Compliance Boundary

This tool is only for backing up data you can already access yourself.

Do not use it to:

- Collect private content from other users
- Bypass CAPTCHA
- Bypass login or permission restrictions
- Perform bulk scraping
- Imply official Douban endorsement

If Douban asks for verification, complete it manually in the browser before continuing.

## 9. FAQ

### Why does Excel display Chinese text correctly now?

The exported Excel CSV includes a UTF-8 BOM, which helps Excel detect the encoding correctly.

### Why is the export not very fast?

The extension uses a request delay to reduce failures and avoid putting unnecessary pressure on Douban.

### Will the export stop if I close the popup?

No. The export runs in the background. Click the extension icon again to check progress.

### Which format should I choose?

Use JSON for long-term backup, Markdown for reading, and Excel CSV for spreadsheet analysis.

### Are notes and reviews guaranteed to be complete?

They are still experimental. Douban page structures may vary, so real account testing is needed to improve accuracy.

