const SCOPES = [
  { key: "book-collect", label: "读过", type: "book" },
  { key: "book-wish", label: "想读", type: "book" },
  { key: "book-do", label: "在读", type: "book" },
  { key: "movie-collect", label: "看过", type: "movie" },
  { key: "movie-wish", label: "想看", type: "movie" },
  { key: "movie-do", label: "在看", type: "movie" },
  { key: "music-collect", label: "听过", type: "music" },
  { key: "music-wish", label: "想听", type: "music" },
  { key: "music-do", label: "在听", type: "music" },
  { key: "statuses", label: "广播", type: "writing" },
  { key: "notes", label: "日记", type: "writing" },
  { key: "reviews", label: "长评", type: "review" }
];

const $ = (selector) => document.querySelector(selector);

const els = {
  userId: $("#userId"),
  scopeList: $("#scopeList"),
  selectCore: $("#selectCore"),
  selectAll: $("#selectAll"),
  clearAll: $("#clearAll"),
  includeDetails: $("#includeDetails"),
  delayMs: $("#delayMs"),
  start: $("#startExport"),
  stop: $("#stopExport"),
  progress: $("#progressBar"),
  status: $("#statusText"),
  log: $("#log")
};

let pollTimer = null;

init();

function init() {
  renderScopes();
  restoreSettings();
  bindEvents();
  initTabs();
  refreshStatus();
  pollTimer = setInterval(refreshStatus, 1200);
  window.addEventListener("unload", () => clearInterval(pollTimer));
}

function bindEvents() {
  els.selectCore.addEventListener("click", selectCoreScopes);
  els.selectAll.addEventListener("click", () => setScopes(() => true));
  els.clearAll.addEventListener("click", () => setScopes(() => false));
  document.querySelectorAll(".filter").forEach((button) => {
    button.addEventListener("click", () => {
      const type = button.dataset.type;
      setScopes((scope) => scope.type === type);
    });
  });
  els.start.addEventListener("click", startExport);
  els.stop.addEventListener("click", stopExport);
}

function renderScopes() {
  els.scopeList.innerHTML = SCOPES.map((scope) => `
    <label class="scope-card">
      <input type="checkbox" value="${scope.key}" checked>
      <strong>${typeName(scope.type)}</strong>
      <span>${scope.label}</span>
    </label>
  `).join("");
}

async function restoreSettings() {
  const saved = await chrome.storage.local.get(["doubanUserId", "delayMs"]);
  if (saved.doubanUserId) els.userId.value = saved.doubanUserId;
  if (saved.delayMs) els.delayMs.value = saved.delayMs;
}

function selectCoreScopes() {
  setScopes((scope) => scope.key.endsWith("collect"));
}

function setScopes(shouldSelect) {
  document.querySelectorAll("#scopeList input").forEach((input) => {
    const scope = SCOPES.find((item) => item.key === input.value);
    input.checked = Boolean(scope && shouldSelect(scope));
  });
}

async function startExport() {
  const userId = els.userId.value.trim();
  const selectedScopes = Array.from(document.querySelectorAll("#scopeList input:checked")).map((input) => input.value);
  const delayMs = Math.max(Number(els.delayMs.value) || 2200, 1200);
  const format = document.querySelector("input[name='format']:checked").value;

  if (!userId) {
    setStatus("请先填写豆瓣用户 ID。");
    return;
  }

  if (selectedScopes.length === 0) {
    setStatus("请至少选择一个导出范围。");
    return;
  }

  await chrome.storage.local.set({ doubanUserId: userId, delayMs });
  const response = await chrome.runtime.sendMessage({
    type: "START_EXPORT",
    payload: {
      userId,
      selectedScopes,
      delayMs,
      format,
      includeDetails: els.includeDetails.checked
    }
  });

  if (!response?.ok) {
    setStatus(response?.error || "启动失败。");
  }
  refreshStatus();
}

async function stopExport() {
  await chrome.runtime.sendMessage({ type: "STOP_EXPORT" });
  setStatus("正在停止，会在当前请求结束后退出。");
  refreshStatus();
}

async function refreshStatus() {
  const state = await chrome.runtime.sendMessage({ type: "GET_STATUS" }).catch(() => null);
  if (!state) return;

  setBusy(state.running);
  setProgress(state.progress || 0);
  setStatus(state.message || "等待开始。");
  els.log.textContent = (state.logs || []).join("\n");
  els.log.scrollTop = els.log.scrollHeight;
}

function typeName(type) {
  return { book: "图书", movie: "电影", music: "音乐", writing: "发布", review: "评价" }[type] || type;
}

function setBusy(isBusy) {
  els.start.disabled = isBusy;
  els.stop.disabled = !isBusy;
}

function setProgress(percent) {
  els.progress.style.width = `${Math.max(0, Math.min(100, percent))}%`;
}

function setStatus(text) {
  els.status.textContent = text;
}

// === AI 资讯 ===

const NEWS_FEEDS = {
  curated: "https://aihot.virxact.com/rss/curated",
  all: "https://aihot.virxact.com/rss/all",
  daily: "https://aihot.virxact.com/rss/daily"
};

let activeFeed = "curated";
const newsCache = {};

function initTabs() {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      const target = tab.dataset.tab;
      document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === target));
      document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.toggle("hidden", panel.id !== `tab-${target}`));
      if (target === "news" && !newsCache[activeFeed]) loadNews();
    });
  });

  document.querySelectorAll(".news-filter").forEach((btn) => {
    btn.addEventListener("click", () => {
      activeFeed = btn.dataset.feed;
      document.querySelectorAll(".news-filter").forEach((b) => b.classList.toggle("active", b.dataset.feed === activeFeed));
      if (!newsCache[activeFeed]) loadNews();
      else renderNews(newsCache[activeFeed]);
    });
  });

  document.getElementById("refreshNews").addEventListener("click", () => {
    delete newsCache[activeFeed];
    loadNews();
  });
}

async function loadNews() {
  const list = document.getElementById("newsList");
  list.innerHTML = '<p class="news-status">加载中…</p>';

  try {
    const res = await fetch(NEWS_FEEDS[activeFeed]);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const xml = await res.text();
    const items = parseRssFeed(xml);
    newsCache[activeFeed] = items;
    renderNews(items);
  } catch (err) {
    list.innerHTML = `<p class="news-status">加载失败：${err.message}</p>`;
  }
}

function parseRssFeed(xml) {
  const doc = new DOMParser().parseFromString(xml, "text/xml");
  return Array.from(doc.querySelectorAll("item")).slice(0, 25).map((item) => {
    const link = item.querySelector("link")?.textContent?.trim()
      || item.querySelector("link")?.getAttribute("href")
      || "";
    return {
      title: item.querySelector("title")?.textContent?.trim() || "",
      link,
      desc: stripHtmlTags(item.querySelector("description")?.textContent || "").replace(/\s+/g, " ").trim(),
      date: item.querySelector("pubDate")?.textContent?.trim() || "",
      source: item.querySelector("source")?.textContent?.trim() || ""
    };
  });
}

function renderNews(items) {
  const list = document.getElementById("newsList");
  if (!items.length) {
    list.innerHTML = '<p class="news-status">暂无内容。</p>';
    return;
  }
  list.innerHTML = items.map((item) => {
    const safeLink = safeUrl(item.link);
    const meta = [item.source, item.date ? relativeTime(item.date) : ""].filter(Boolean).join(" · ");
    return `<a class="news-card" href="${safeLink}" target="_blank" rel="noopener noreferrer">
      <div class="news-card-title">${htmlEscape(item.title)}</div>
      ${item.desc ? `<div class="news-card-desc">${htmlEscape(item.desc)}</div>` : ""}
      ${meta ? `<div class="news-card-meta">${htmlEscape(meta)}</div>` : ""}
    </a>`;
  }).join("");
}

function relativeTime(dateStr) {
  try {
    const diff = Date.now() - new Date(dateStr).getTime();
    if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`;
    const d = new Date(dateStr);
    return `${d.getMonth() + 1}月${d.getDate()}日`;
  } catch {
    return "";
  }
}

function htmlEscape(text) {
  return String(text ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function safeUrl(url) {
  try {
    const parsed = new URL(url);
    if (parsed.protocol !== "https:" && parsed.protocol !== "http:") return "#";
    return parsed.href;
  } catch {
    return "#";
  }
}

function stripHtmlTags(text) {
  return text.replace(/<[^>]+>/g, " ");
}
