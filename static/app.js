const I18N = {
  zh: {
    appTitle: "本地站点预览器",
    appSubtitle: "加载 ZIP 与 SQL，一键启动本地服务器预览",
    step1Title: "选择 ZIP 源码包",
    step1Lead: "点击按钮弹出文件管理器，选择包含网站源码的 ZIP。",
    pickZip: "选择 ZIP 文件",
    zipHint: "尚未选择",
    step2Title: "选择 SQL 文件",
    step2Lead: "选择数据库导入文件（可选但推荐）。",
    pickSql: "选择 SQL 文件",
    sqlHint: "尚未选择",
    step3Title: "服务器设定",
    step3Lead: "根据项目自动检测，可调整 PHP 相关选项。",
    phpVerLabel: "PHP 版本（如可用）",
    extLabel: "启用扩展（如适用）",
    step4Title: "启动预览",
    step4Lead: "按钮已就绪。点击后将解压、导入并启动临时本地服务器，然后打开默认浏览器。",
    startBtn: "启动预览并打开浏览器",
    openAgain: "再次打开浏览器",
    stopBtn: "停止并清理",
    restart: "重新开始",
    next: "下一步",
    back: "上一步",
    themeGold: "黑金",
    themeLight: "浅色",
    selected: "已选择：",
    noPhp: "未检测到系统 PHP，将使用纯静态服务器。",
    hasPhp: "检测到 PHP，将优先使用 php -S。",
    starting: "正在启动…",
    running: "预览已启动",
    stopped: "已停止并清理",
  },
  en: {
    appTitle: "Site Preview Desk",
    appSubtitle: "Load a ZIP + SQL, start a temporary local server and preview in your browser",
    step1Title: "Select ZIP package",
    step1Lead: "Click to open the file dialog and choose the website source ZIP.",
    pickZip: "Choose ZIP file",
    zipHint: "None selected",
    step2Title: "Select SQL file",
    step2Lead: "Choose the database import file (optional but recommended).",
    pickSql: "Choose SQL file",
    sqlHint: "None selected",
    step3Title: "Server settings",
    step3Lead: "Auto-detected from the project. Adjust PHP options if applicable.",
    phpVerLabel: "PHP version (if available)",
    extLabel: "Extensions to enable (if applicable)",
    step4Title: "Launch preview",
    step4Lead: "Ready. Click to extract, import, start a temporary local server, and open your default browser.",
    startBtn: "Start preview & open browser",
    openAgain: "Open browser again",
    stopBtn: "Stop & clean up",
    next: "Next",
    restart: "Start over",
    back: "Back",
    themeGold: "Gold",
    themeLight: "Light",
    selected: "Selected: ",
    noPhp: "No system PHP detected. Falling back to static server.",
    hasPhp: "PHP detected. Will prefer php -S.",
    starting: "Starting…",
    running: "Preview running",
    stopped: "Stopped and cleaned",
  },
};

let uiLang = localStorage.getItem("aio.uiLang") || (navigator.language.startsWith("zh") ? "zh" : "en");
let currentStep = 0;
const LAST = 3;
let zipPath = "";
let sqlPath = "";

function t(key) { return (I18N[uiLang] || I18N.en)[key] || key; }

function applyI18n() {
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const k = el.getAttribute("data-i18n");
    if (k && t(k)) el.textContent = t(k);
  });
  document.documentElement.lang = uiLang === "zh" ? "zh-CN" : "en";
}

function renderStepNav() {
  const nav = document.getElementById("stepNav");
  nav.innerHTML = "";
  const labels = ["ZIP", "SQL", t("step3Title"), t("step4Title")];
  for (let i = 0; i <= LAST; i++) {
    const pill = document.createElement("div");
    pill.className = "step-pill" + (i === currentStep ? " on" : "") + (i < currentStep ? " done" : "");
    pill.textContent = (i + 1) + " " + labels[i];
    nav.appendChild(pill);
  }
}

function goStep(n) {
  currentStep = n;
  document.querySelectorAll(".wizard-card").forEach(c => c.classList.remove("on"));
  document.getElementById("stage" + n)?.classList.add("on");
  const rb = document.getElementById("restartBtn");
  if (rb) rb.hidden = n < 1;
  renderStepNav();
  applyI18n();
  savePrefs();
}

async function restartAll() {
  try { await fetch("/api/stop_preview", { method: "POST" }); } catch (e) {}
  zipPath = "";
  sqlPath = "";
  const zh = document.getElementById("zipHint");
  const sh = document.getElementById("sqlHint");
  if (zh) zh.textContent = t("zipHint");
  if (sh) sh.textContent = t("sqlHint");
  const n1 = document.getElementById("next1");
  if (n1) n1.disabled = true;
  const st = document.getElementById("statusHint");
  if (st) st.textContent = "";
  const rb = document.getElementById("runningBox");
  if (rb) rb.hidden = true;
  const ov = document.getElementById("previewOverlay");
  if (ov) ov.hidden = true;
  const fr = document.getElementById("previewFrame");
  if (fr) fr.src = "about:blank";
  const db = document.getElementById("detectBox");
  if (db) db.innerHTML = "";
  try { localStorage.removeItem("site-preview-desk.prefs"); } catch (e) {}
  goStep(0);
}

function savePrefs() {
  const prefs = {
    theme: document.documentElement.getAttribute("data-theme") || "gold",
    zipPath, sqlPath, step: currentStep,
  };
  localStorage.setItem("site-preview-desk.prefs", JSON.stringify(prefs));
}

function loadPrefs() {
  try {
    const p = JSON.parse(localStorage.getItem("site-preview-desk.prefs") || "{}");
    if (p.theme) {
      document.documentElement.setAttribute("data-theme", p.theme);
      document.getElementById("themeSwitch").setAttribute("data-on", p.theme);
    }
    if (p.zipPath) { zipPath = p.zipPath; document.getElementById("zipHint").textContent = t("selected") + zipPath; document.getElementById("next1").disabled = false; }
    if (p.sqlPath) { sqlPath = p.sqlPath; document.getElementById("sqlHint").textContent = t("selected") + sqlPath; }
  } catch {}
}

async function pickZip() {
  if (window.pywebview && pywebview.api && pywebview.api.select_file) {
    const path = await pywebview.api.select_file("zip");
    if (path) {
      zipPath = path;
      document.getElementById("zipHint").textContent = t("selected") + path;
      document.getElementById("next1").disabled = false;
      savePrefs();
    }
  } else {
    alert("File dialog requires the desktop window (pywebview).");
  }
}

async function pickSql() {
  if (window.pywebview && pywebview.api && pywebview.api.select_file) {
    const path = await pywebview.api.select_file("sql");
    if (path) {
      sqlPath = path;
      document.getElementById("sqlHint").textContent = t("selected") + path;
      savePrefs();
    }
  } else {
    alert("File dialog requires the desktop window.");
  }
}

async function loadSettings() {
  try {
    const r = await fetch("/api/analyze", { method: "POST" });
    const data = await r.json();
    const box = document.getElementById("detectBox");
    box.innerHTML = (data.has_php ? t("hasPhp") : t("noPhp")) +
      "<br>Files: " + (data.file_count || 0) +
      (data.php_version ? "<br>" + data.php_version : "");
    document.getElementById("phpVer").value = data.php_version || "—";
    const list = document.getElementById("extList");
    list.innerHTML = "";
    (data.suggested_extensions || []).forEach(ext => {
      const lab = document.createElement("label");
      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.value = ext;
      cb.checked = true;
      lab.appendChild(cb);
      lab.appendChild(document.createTextNode(ext));
      list.appendChild(lab);
    });
  } catch (e) {
    document.getElementById("detectBox").textContent = "Analyze failed: " + e;
  }
}

async function startPreview() {
  const hint = document.getElementById("statusHint");
  hint.textContent = t("starting");
  const exts = Array.from(document.querySelectorAll("#extList input:checked")).map(c => c.value);
  const body = { php_version: document.getElementById("phpVer").value, extensions: exts, docroot: "." };
  try {
    const r = await fetch("/api/start_preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || "start failed");
    hint.textContent = t("running") + " — " + data.url;
    document.getElementById("runningBox").hidden = false;
    document.getElementById("urlShow").textContent = data.url + (data.db_info ? " | " + data.db_info : "");
    // Show inside the app, not an external browser
    document.getElementById("previewUrlLabel").textContent = data.url;
    document.getElementById("previewFrame").src = data.url;
    document.getElementById("previewOverlay").hidden = false;
  } catch (e) {
    hint.textContent = String(e);
  }
}

async function stopPreview() {
  await fetch("/api/stop_preview", { method: "POST" });
  document.getElementById("statusHint").textContent = t("stopped");
  document.getElementById("runningBox").hidden = true;
}

document.getElementById("pickZip").onclick = pickZip;
document.getElementById("restartBtn").onclick = restartAll;
document.getElementById("pickSql").onclick = pickSql;
document.getElementById("next1").onclick = () => goStep(1);
document.getElementById("back2").onclick = () => goStep(0);
document.getElementById("next2").onclick = () => { loadSettings(); goStep(2); };
document.getElementById("back3").onclick = () => goStep(1);
document.getElementById("next3").onclick = () => goStep(3);
document.getElementById("back4").onclick = () => goStep(2);
document.getElementById("startBtn").onclick = startPreview;
document.getElementById("stopBtn").onclick = stopPreview;
document.getElementById("openAgain").onclick = () => {
  const raw = document.getElementById("urlShow").textContent || "";
  const u = raw.split(" ")[0];
  if (u) {
    document.getElementById("previewUrlLabel").textContent = u;
    document.getElementById("previewFrame").src = u;
    document.getElementById("previewOverlay").hidden = false;
  }
};

document.getElementById("closePreview").onclick = async () => {
  document.getElementById("previewOverlay").hidden = true;
  document.getElementById("previewFrame").src = "about:blank";
  await stopPreview();
};

document.querySelectorAll("#themeSwitch button").forEach(btn => {
  btn.onclick = () => {
    const next = btn.getAttribute("data-theme");
    document.documentElement.setAttribute("data-theme", next);
    document.getElementById("themeSwitch").setAttribute("data-on", next);
    savePrefs();
  };
});

document.querySelectorAll("#uiLangSwitch button").forEach(btn => {
  btn.onclick = () => {
    uiLang = btn.getAttribute("data-ui-lang");
    localStorage.setItem("aio.uiLang", uiLang);
    document.querySelectorAll("#uiLangSwitch button").forEach(b => b.classList.toggle("on", b === btn));
    applyI18n();
    renderStepNav();
  };
});

// Init
loadPrefs();
applyI18n();
renderStepNav();
fetch("/api/defaults").then(r => r.json()).then(d => {
  document.getElementById("appVersion").textContent = "v" + (d.version || "1.0.0");
});
