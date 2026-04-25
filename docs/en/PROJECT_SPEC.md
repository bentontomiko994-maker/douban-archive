# Project Spec: Douban Archive

## One-liner

Export a user's own Douban book, movie, and music records into local files for personal backup and future AI-powered interest profiling.

## Users

The primary users are active Douban users and people who worry about platform decline, feature shutdowns, or losing access to their own cultural history.

## MVP Scope

The first phase focuses on book, movie, and music collections:

- Books: collected, wish, doing
- Movies: collected, wish, doing
- Music: collected, wish, doing

v0.2.0 adds experimental export entries for:

- Statuses / broadcasts
- Notes

v0.3.0 adds:

- Normalized rating export
- Short comments, long reviews, and full note content
- Select-all and category-based selection controls
- Chinese text displays correctly when opening CSV directly in Excel

Group posts and comments are intentionally deferred.

## Principles

- Local first
- Privacy first
- No user data upload
- No bypassing platform access controls
- Export tasks should continue in the background after the popup closes
- Prefer a working, exportable, and maintainable MVP

## Acceptance Criteria

- The user can load the extension in a Chromium browser
- The user can enter a Douban user ID
- The user can choose export scopes
- The user can select all content or choose books, movies, music, writing, and reviews by category
- The user can export JSON, Excel CSV, or Markdown
- Exported records include title, URL, rating, rating ratio, tags, short comments, long review content, note content, and date when available
- The background export continues after the extension popup closes
- The repository includes bilingual English and Chinese documentation
