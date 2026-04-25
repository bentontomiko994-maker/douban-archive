const SCOPES = [
  { key: "book-collect", domain: "book", label: "读过", type: "book", status: "collect", kind: "collection" },
  { key: "book-wish", domain: "book", label: "想读", type: "book", status: "wish", kind: "collection" },
  { key: "book-do", domain: "book", label: "在读", type: "book", status: "do", kind: "collection" },
  { key: "movie-collect", domain: "movie", label: "看过", type: "movie", status: "collect", kind: "collection" },
  { key: "movie-wish", domain: "movie", label: "想看", type: "movie", status: "wish", kind: "collection" },
  { key: "movie-do", domain: "movie", label: "在看", type: "movie", status: "do", kind: "collection" },
  { key: "music-collect", domain: "music", label: "听过", type: "music", status: "collect", kind: "collection" },
  { key: "music-wish", domain: "music", label: "想听", type: "music", status: "wish", kind: "collection" },
  { key: "music-do", domain: "music", label: "在听", type: "music", status: "do", kind: "collection" },
  { key: "statuses", label: "广播", type: "status", kind: "statuses" },
  { key: "notes", label: "日记", type: "note", kind: "notes" },
  { key: "reviews", label: "长评", type: "review", kind: "reviews" }
];

const PAGE_SIZE = 15;
const state = {
  running: false,
  stopRequested: false,
  progress: 0,
  message: "等待开始。",
  logs: [],
  archive: null
};

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === "GET_STATUS") {
    sendResponse(snapshot());
    return false;
  }

  if (message.type === "STOP_EXPORT") {
    state.stopRequested = true;
    state.message = "正在停止，会在当前请求结束后退出。";
    sendResponse({ ok: true });
    return false;
  }

  if (message.type === "START_EXPORT") {
    if (state.running) {
      sendResponse({ ok: false, error: "已有导出任务正在后台运行。" });
      return false;
    }
    runExport(message.payload);
    sendResponse({ ok: true });
    return false;
  }

  return false;
});

async function runExport(options) {
  const scopes = SCOPES.filter((scope) => options.selectedScopes.includes(scope.key));
  resetState(options.userId);
  state.running = true;
  state.message = "后台导出已启动。你可以关闭弹窗，任务会继续运行。";

  try {
    for (let i = 0; i < scopes.length; i += 1) {
      if (state.stopRequested) break;
      const scope = scopes[i];
      setProgress((i / scopes.length) * 92);
      state.message = `正在导出 ${typeName(scope.type)} · ${scope.label}`;
      const result = await exportScope(options.userId, scope, options.delayMs, options.includeDetails);
      state.archive.items.push(...result.items);
      state.archive.errors.push(...result.errors);
    }

    if (state.archive.items.length === 0 && state.archive.errors.length > 0) {
      throw new Error("没有成功导出任何条目，请确认已登录豆瓣，用户 ID 正确，相关页面可以在浏览器中打开。");
    }

    const file = buildFile(state.archive, options.format);
    await downloadFile(file.filename, file.content, file.mime);
    setProgress(100);
    state.message = `完成：导出 ${state.archive.items.length} 条，错误 ${state.archive.errors.length} 条。文件已保存到浏览器下载目录。`;
  } catch (error) {
    state.message = error.message || String(error);
    logLine(`ERROR ${error.stack || error.message || error}`);
  } finally {
    state.running = false;
    state.stopRequested = false;
  }
}

function resetState(userId) {
  state.running = false;
  state.stopRequested = false;
  state.progress = 0;
  state.logs = [];
  state.archive = {
    meta: {
      tool: "Douban Archive",
      version: "0.3.1",
      userId,
      exportedAt: new Date().toISOString(),
      formatVersion: 1,
      privacy: "local-only"
    },
    items: [],
    errors: []
  };
}

async function exportScope(userId, scope, delayMs, includeDetails) {
  const items = [];
  const errors = [];
  let page = 1;
  let start = 0;

  while (!state.stopRequested) {
    const url = buildScopeUrl(userId, scope, page, start);
    logLine(`GET ${url}`);

    try {
      const html = await fetchText(url);
      const pageItems = parsePage(html, scope, url);

      if (pageItems.length === 0) break;

      for (const item of pageItems) {
        if (state.stopRequested) break;
        const shouldFetchDetail = item.url && (includeDetails || scope.kind === "notes" || scope.kind === "reviews");
        if (shouldFetchDetail) {
          await sleep(delayMs);
          item.detail = await fetchDetail(item.url, scope.kind).catch((error) => {
            errors.push({ scope: scope.key, url: item.url, message: error.message });
            return null;
          });
        }
        items.push(item);
      }

      state.message = `已导出 ${typeName(scope.type)} · ${scope.label}：${items.length} 条`;
      if (!hasNextPage(html)) break;

      page += 1;
      start += PAGE_SIZE;
      await sleep(delayMs);
    } catch (error) {
      errors.push({ scope: scope.key, page, url, message: error.message });
      logLine(`ERROR ${scope.key} page ${page}: ${error.message}`);
      break;
    }
  }

  return { items, errors };
}

function buildScopeUrl(userId, scope, page, start) {
  if (scope.kind === "statuses") {
    return `https://www.douban.com/people/${encodeURIComponent(userId)}/statuses?p=${page}`;
  }
  if (scope.kind === "notes") {
    return `https://www.douban.com/people/${encodeURIComponent(userId)}/notes?start=${start}`;
  }
  if (scope.kind === "reviews") {
    return `https://www.douban.com/people/${encodeURIComponent(userId)}/reviews?start=${start}`;
  }
  const params = new URLSearchParams({
    start: String(start),
    sort: "time",
    rating: "all",
    filter: "all",
    mode: "grid"
  });
  return `https://${scope.domain}.douban.com/people/${encodeURIComponent(userId)}/${scope.status}?${params}`;
}

async function fetchText(url) {
  const response = await fetch(url, {
    credentials: "include",
    headers: { "Accept": "text/html,application/xhtml+xml" }
  });

  if (!response.ok) throw new Error(`请求失败：HTTP ${response.status}`);

  const text = await response.text();
  if (looksBlocked(text)) {
    throw new Error("页面可能需要验证或登录，请在浏览器中打开豆瓣确认后再试。");
  }
  return text;
}

async function fetchDetail(url, kind = "collection") {
  const html = await fetchText(url);
  if (kind === "notes") return parseNoteDetail(html, url);
  if (kind === "reviews") return parseReviewDetail(html, url);
  return {
    title: cleanText(firstMatch(html, /<h1[^>]*>([\s\S]*?)<\/h1>/i)),
    summary: cleanText(firstMatch(html, /<div[^>]+id=["']link-report["'][^>]*>([\s\S]*?)<\/div>/i))
      || cleanText(firstMatch(html, /<div[^>]+id=["']info["'][^>]*>([\s\S]*?)<\/div>/i)),
    fetchedAt: new Date().toISOString()
  };
}

function parsePage(html, scope, sourceUrl) {
  if (scope.kind === "statuses") return parseStatuses(html, scope, sourceUrl);
  if (scope.kind === "notes") return parseNotes(html, scope, sourceUrl);
  if (scope.kind === "reviews") return parseReviews(html, scope, sourceUrl);
  return parseCollectionPage(html, scope, sourceUrl);
}

function parseCollectionPage(html, scope, sourceUrl) {
  const blocks = splitBlocks(html, /<li[^>]+class=["'][^"']*\b(?:subject-item|item)[^"']*["'][^>]*>/gi, "</li>");
  const fallbackBlocks = blocks.length ? blocks : splitBlocks(html, /<div[^>]+class=["'][^"']*\bitem\b[^"']*["'][^>]*>/gi, "</div>");

  return fallbackBlocks.map((block) => {
    const link = extractSubjectLink(block);
    const title = cleanText(firstMatch(block, /<em[^>]*>([\s\S]*?)<\/em>/i))
      || cleanText(firstMatch(block, /<a[^>]+title=["']([^"']+)["'][^>]*>/i))
      || cleanText(firstMatch(block, /<a[^>]*>([\s\S]*?)<\/a>/i));
    const cover = normalizeUrl(firstMatch(block, /<img[^>]+src=["']([^"']+)["']/i));
    const rating = parseRating(block);
    const comment = cleanText(firstMatch(block, /<span[^>]+class=["'][^"']*(?:comment|short-note|intro)[^"']*["'][^>]*>([\s\S]*?)<\/span>/i));
    const date = cleanText(firstMatch(block, /<span[^>]+class=["'][^"']*date[^"']*["'][^>]*>([\s\S]*?)<\/span>/i));
    const tags = cleanText(firstMatch(block, /<span[^>]+class=["'][^"']*tags[^"']*["'][^>]*>([\s\S]*?)<\/span>/i))
      .replace(/^标签[:：]\s*/, "")
      .split(/\s+/)
      .filter(Boolean);

    return {
      id: extractDoubanId(link),
      type: scope.type,
      status: scope.status,
      statusLabel: scope.label,
      title,
      url: link,
      cover,
      rating,
      ratingValue: rating,
      ratingMax: rating ? 5 : null,
      ratingPercent: rating ? rating / 5 : null,
      comment,
      shortReview: comment,
      tags,
      collectedAt: date,
      sourceUrl,
      exportedAt: new Date().toISOString()
    };
  }).filter((item) => item.title || item.url);
}

function parseStatuses(html, scope, sourceUrl) {
  const blocks = splitBlocks(html, /<div[^>]+class=["'][^"']*\bstatus-item\b[^"']*["'][^>]*>/gi, "</div>");
  return blocks.map((block) => {
    const url = normalizeUrl(firstMatch(block, /<a[^>]+href=["']([^"']*\/status\/\d+\/?[^"']*)["']/i));
    return {
      id: url.match(/status\/(\d+)/)?.[1] || "",
      type: scope.type,
      status: "published",
      statusLabel: scope.label,
      title: "豆瓣广播",
      url,
      content: cleanText(firstMatch(block, /<blockquote[^>]*>([\s\S]*?)<\/blockquote>/i)) || cleanText(block),
      publishedAt: cleanText(firstMatch(block, /<span[^>]+class=["'][^"']*created_at[^"']*["'][^>]*>([\s\S]*?)<\/span>/i)),
      sourceUrl,
      exportedAt: new Date().toISOString()
    };
  }).filter((item) => item.content || item.url);
}

function parseNotes(html, scope, sourceUrl) {
  const noteLinks = Array.from(html.matchAll(/<a[^>]+href=["']([^"']*\/note\/\d+\/?[^"']*)["'][^>]*>([\s\S]*?)<\/a>/gi));
  const seen = new Set();
  return noteLinks.map((match) => {
    const url = normalizeUrl(match[1]);
    if (seen.has(url)) return null;
    seen.add(url);
    return {
      id: url.match(/note\/(\d+)/)?.[1] || "",
      type: scope.type,
      status: "published",
      statusLabel: scope.label,
      title: cleanText(match[2]),
      url,
      sourceUrl,
      exportedAt: new Date().toISOString()
    };
  }).filter(Boolean);
}

function parseReviews(html, scope, sourceUrl) {
  const reviewLinks = Array.from(html.matchAll(/<a[^>]+href=["']([^"']*\/review\/\d+\/?[^"']*)["'][^>]*>([\s\S]*?)<\/a>/gi));
  const seen = new Set();
  return reviewLinks.map((match) => {
    const url = normalizeUrl(match[1]);
    if (seen.has(url)) return null;
    seen.add(url);
    const surrounding = sliceAround(html, match.index, 1200);
    const rating = parseRating(surrounding);
    return {
      id: url.match(/review\/(\d+)/)?.[1] || "",
      type: scope.type,
      status: "published",
      statusLabel: scope.label,
      title: cleanText(match[2]),
      url,
      rating,
      ratingValue: rating,
      ratingMax: rating ? 5 : null,
      ratingPercent: rating ? rating / 5 : null,
      excerpt: cleanText(firstMatch(surrounding, /<div[^>]+class=["'][^"']*(?:short-content|review-short)[^"']*["'][^>]*>([\s\S]*?)<\/div>/i)),
      publishedAt: cleanText(firstMatch(surrounding, /<span[^>]+class=["'][^"']*(?:main-meta|created_at|time)[^"']*["'][^>]*>([\s\S]*?)<\/span>/i)),
      sourceUrl,
      exportedAt: new Date().toISOString()
    };
  }).filter(Boolean);
}

function parseNoteDetail(html, url) {
  return {
    title: cleanText(firstMatch(html, /<h1[^>]*>([\s\S]*?)<\/h1>/i)),
    content: cleanText(firstMatch(html, /<div[^>]+id=["']link-report["'][^>]*>([\s\S]*?)<\/div>/i))
      || cleanText(firstMatch(html, /<div[^>]+class=["'][^"']*(?:note|article)[^"']*["'][^>]*>([\s\S]*?)<\/div>/i)),
    publishedAt: cleanText(firstMatch(html, /<span[^>]+class=["'][^"']*(?:pub-date|created_at|time)[^"']*["'][^>]*>([\s\S]*?)<\/span>/i)),
    url,
    fetchedAt: new Date().toISOString()
  };
}

function parseReviewDetail(html, url) {
  const rating = parseRating(html);
  return {
    title: cleanText(firstMatch(html, /<h1[^>]*>([\s\S]*?)<\/h1>/i)),
    content: cleanText(firstMatch(html, /<div[^>]+class=["'][^"']*review-content[^"']*["'][^>]*>([\s\S]*?)<\/div>/i))
      || cleanText(firstMatch(html, /<div[^>]+id=["']link-report["'][^>]*>([\s\S]*?)<\/div>/i)),
    rating,
    ratingValue: rating,
    ratingMax: rating ? 5 : null,
    ratingPercent: rating ? rating / 5 : null,
    publishedAt: cleanText(firstMatch(html, /<span[^>]+class=["'][^"']*(?:main-meta|created_at|time)[^"']*["'][^>]*>([\s\S]*?)<\/span>/i)),
    url,
    fetchedAt: new Date().toISOString()
  };
}

function splitBlocks(html, startPattern, endTag) {
  const blocks = [];
  const starts = Array.from(html.matchAll(startPattern));
  for (const startMatch of starts) {
    const start = startMatch.index;
    const end = html.indexOf(endTag, start + startMatch[0].length);
    if (end > start) blocks.push(html.slice(start, end + endTag.length));
  }
  return blocks;
}

function sliceAround(text, index, radius) {
  return text.slice(Math.max(0, index - radius), Math.min(text.length, index + radius));
}

function hasNextPage(html) {
  return /class=["'][^"']*\bnext\b[^"']*["'][\s\S]*?<a\b/i.test(html)
    || /rel=["']next["']/i.test(html);
}

function looksBlocked(html) {
  return /检测到有异常请求|请输入验证码|sec\.douban\.com|登录豆瓣/.test(html);
}

function buildFile(archive, format) {
  const date = new Date().toISOString().slice(0, 10);
  if (format === "csv") {
    return {
      filename: `douban-archive-${archive.meta.userId}-${date}.csv`,
      mime: "text/csv;charset=utf-8",
      content: toCsv(archive.items)
    };
  }
  if (format === "md") {
    return {
      filename: `douban-archive-${archive.meta.userId}-${date}.md`,
      mime: "text/markdown;charset=utf-8",
      content: toMarkdown(archive)
    };
  }
  return {
    filename: `douban-archive-${archive.meta.userId}-${date}.json`,
    mime: "application/json;charset=utf-8",
    content: JSON.stringify(archive, null, 2)
  };
}

function toCsv(items) {
  const headers = ["id", "type", "status", "statusLabel", "title", "url", "ratingValue", "ratingMax", "ratingPercent", "comment", "content", "detailContent", "tags", "collectedAt", "publishedAt"];
  const rows = items.map((item) => headers.map((key) => csvCell(getCsvValue(item, key))));
  const csvBody = [headers.join(","), ...rows.map((row) => row.join(","))].join("\r\n");
  return `\uFEFF${csvBody}`;
}

function getCsvValue(item, key) {
  if (key === "detailContent") return item.detail?.content || item.detail?.summary || "";
  const value = item[key];
  return Array.isArray(value) ? value.join(" ") : value;
}

function toMarkdown(archive) {
  const lines = [
    `# Douban Archive: ${archive.meta.userId}`,
    "",
    `Exported at: ${archive.meta.exportedAt}`,
    "",
    `Total items: ${archive.items.length}`,
    ""
  ];

  for (const item of archive.items) {
    lines.push(`## ${item.title || item.statusLabel || "Untitled"}`);
    lines.push("");
    lines.push(`- Type: ${item.type}`);
    lines.push(`- Status: ${item.statusLabel || item.status || ""}`);
    if (item.ratingValue) lines.push(`- Rating: ${item.ratingValue}/${item.ratingMax || 5}`);
    if (item.collectedAt) lines.push(`- Date: ${item.collectedAt}`);
    if (item.publishedAt) lines.push(`- Published: ${item.publishedAt}`);
    if (item.url) lines.push(`- URL: ${item.url}`);
    if (item.tags?.length) lines.push(`- Tags: ${item.tags.join(", ")}`);
    const body = item.comment || item.content || item.detail?.content || item.detail?.summary || item.excerpt;
    if (body) lines.push("", body);
    lines.push("");
  }

  return lines.join("\n");
}

async function downloadFile(filename, content, mime) {
  const dataUrl = `data:${mime},${encodeURIComponent(content)}`;
  await chrome.downloads.download({ url: dataUrl, filename, saveAs: true });
}

function extractSubjectLink(block) {
  const direct = firstMatch(block, /<a[^>]+href=["']([^"']*\/subject\/\d+\/?[^"']*)["']/i);
  return normalizeUrl(direct || firstMatch(block, /<a[^>]+href=["']([^"']+)["']/i));
}

function parseRating(block) {
  const allstar = firstMatch(block, /class=["'][^"']*allstar(\d+)[^"']*["']/i);
  if (allstar) return normalizeRatingNumber(Number(allstar));

  const rating = firstMatch(block, /class=["'][^"']*rating(\d+)-t[^"']*["']/i);
  if (rating) return normalizeRatingNumber(Number(rating));

  const textRating = firstMatch(block, /(\d(?:\.\d)?)\s*星/);
  return textRating ? normalizeRatingNumber(Number(textRating)) : null;
}

function normalizeRatingNumber(value) {
  if (!Number.isFinite(value) || value <= 0) return null;
  if (value > 10) return Math.min(5, value / 10);
  return Math.min(5, value);
}

function firstMatch(text, pattern) {
  return text.match(pattern)?.[1] || "";
}

function csvCell(value) {
  const text = value == null ? "" : String(value);
  return `"${text.replaceAll('"', '""')}"`;
}

function normalizeUrl(url) {
  if (!url) return "";
  try {
    return new URL(url, "https://www.douban.com").href;
  } catch {
    return url;
  }
}

function extractDoubanId(url) {
  return url?.match(/subject\/(\d+)/)?.[1] || "";
}

function cleanText(text) {
  return decodeHtml(stripTags(text || "")).replace(/\s+/g, " ").trim();
}

function stripTags(text) {
  return text.replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ");
}

function decodeHtml(text) {
  return text.replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function typeName(type) {
  return { book: "图书", movie: "电影", music: "音乐", status: "广播", note: "日记" }[type] || type;
}

function setProgress(percent) {
  state.progress = Math.max(0, Math.min(100, percent));
}

function logLine(text) {
  const time = new Date().toLocaleTimeString();
  state.logs.push(`[${time}] ${text}`);
  state.logs = state.logs.slice(-80);
}

function snapshot() {
  return {
    running: state.running,
    progress: state.progress,
    message: state.message,
    logs: state.logs,
    itemCount: state.archive?.items.length || 0,
    errorCount: state.archive?.errors.length || 0
  };
}
