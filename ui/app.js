const I18N = {
  id: {
    "nav.home": "Beranda", "nav.projects": "Proyek", "nav.voice": "Suara", "nav.models": "Model", "nav.settings": "Pengaturan",
    "common.refresh": "Muat ulang", "common.back": "Kembali", "common.save": "Simpan", "common.cancel": "Batal",
    "common.delete": "Hapus", "common.render": "Render", "common.edit": "Edit", "common.close": "Tutup", "common.preview": "Pratinjau",
    "home.title": "Buat klip dari video apa pun",
    "home.lead": "Tempel link YouTube / TikTok / Instagram atau pilih berkas video lokal. Klip 9:16, subtitle otomatis, dan voiceover dibuat lokal di perangkatmu.",
    "home.source": "Link atau lokasi berkas", "home.pick": "Pilih berkas", "home.count": "Jumlah klip",
    "home.lang": "Bahasa konten", "home.min": "Durasi minimum (detik)", "home.max": "Durasi maksimum (detik)",
    "home.transcript": "Transkrip otomatis (subtitle)", "home.llm": "Pakai LLM lokal untuk pilih momen",
    "home.start": "Mulai buat klip", "home.doctor": "Cek perangkat", "home.recent": "Proyek terakhir",
    "home.quality": "Kualitas video", "home.advanced": "Pengaturan lanjutan",
    "home.linkReading": "Membaca link…", "home.linkReady": "Link siap", "home.linkFail": "Link tidak bisa dibaca",
    "home.localReady": "Berkas lokal siap",
    "projects.title": "Proyek", "projects.export": "Export gabungan", "projects.empty": "Belum ada proyek. Buat dari halaman Beranda.",
    "projects.deleteConfirm": "Hapus proyek ini beserta semua klipnya?",
    "clips.deleteConfirm": "Hapus klip ini? Berkas hasil rendernya ikut dihapus.",
    "clips.deleted": "Klip dihapus.",
    "editor.timeline": "Timeline", "editor.addText": "Tambah teks", "editor.addMedia": "Tambah media", "editor.addMusic": "Tambah musik",
    "editor.template": "Template teks", "editor.previewDraft": "Pratinjau cepat", "editor.deleteItem": "Hapus item",
    "timeline.video": "Video", "timeline.media": "Media", "timeline.text": "Teks", "timeline.audio": "Audio",
    "voice.title": "Suara otomatis",
    "voice.lead": "Buat voiceover Bahasa Indonesia atau Inggris dengan Piper (super ringan), atau kloning suaramu sendiri dengan Chatterbox.",
    "voice.tts": "Text to speech", "voice.text": "Teks", "voice.lang": "Bahasa", "voice.model": "Model suara",
    "voice.generate": "Buat suara", "voice.clone": "Kloning suara",
    "voice.cloneNote": "Gunakan hanya suara milikmu sendiri atau yang kamu punya izin. Output otomatis mengandung watermark PerTh.",
    "voice.sample": "Contoh rekaman (wav/mp3, 10-30 detik)", "voice.cloneRun": "Kloning", "voice.result": "Hasil",
    "models.title": "Model",
    "models.lead": "Model tidak dibundel dalam aplikasi. Studio ZAI mendeteksi perangkatmu dan menyarankan model paling ringan yang cocok.",
    "models.download": "Unduh", "models.remove": "Hapus", "models.installed": "terpasang", "models.pip": "via pip",
    "models.recommended": "rekomendasi",
    "models.kindAsr": "Transkripsi", "models.kindTts": "Suara", "models.kindClone": "Kloning suara",
    "settings.title": "Pengaturan", "settings.lang": "Bahasa antarmuka", "settings.asr": "Model transkripsi default",
    "settings.tts": "Suara Indonesia default", "settings.clone": "Model kloning default", "settings.crop": "Mode crop default",
    "settings.cookies": "cookies.txt (opsional, untuk video privat)",
    "settings.llm": "LLM lokal (opsional)", "settings.llmNote": "Untuk pemilihan momen yang lebih pintar. Contoh Ollama: http://127.0.0.1:11434/v1",
    "settings.consent": "Saya hanya mengkloning suara milik saya atau yang saya punya izin.",
    "settings.openData": "Buka folder data",
    "editor.trim": "Potong (detik)", "editor.crop": "Framing", "editor.subtitleStyle": "Gaya subtitle",
    "editor.captions": "Caption (start|end|teks per baris)", "editor.audio": "Audio",
    "editor.narration": "Teks narasi untuk klip ini", "editor.ttsClip": "Buat suara untuk klip", "editor.cloneClip": "Kloning untuk klip",
    "audio.original": "Audio asli", "audio.voice": "Narasi saja", "audio.mix": "Narasi + audio asli",
    "toast.done": "Selesai", "toast.error": "Terjadi kesalahan", "toast.saved": "Tersimpan",
  },
  en: {
    "nav.home": "Home", "nav.projects": "Projects", "nav.voice": "Voice", "nav.models": "Models", "nav.settings": "Settings",
    "common.refresh": "Refresh", "common.back": "Back", "common.save": "Save", "common.cancel": "Cancel",
    "common.delete": "Delete", "common.render": "Render", "common.edit": "Edit", "common.close": "Close", "common.preview": "Preview",
    "home.title": "Turn any video into clips",
    "home.lead": "Paste a YouTube / TikTok / Instagram link or pick a local video file. 9:16 clips, automatic subtitles and voiceover — all local.",
    "home.source": "Link or file path", "home.pick": "Pick file", "home.count": "Number of clips",
    "home.lang": "Content language", "home.min": "Minimum length (seconds)", "home.max": "Maximum length (seconds)",
    "home.transcript": "Automatic transcript (subtitles)", "home.llm": "Use local LLM to pick moments",
    "home.start": "Start clipping", "home.doctor": "Check device", "home.recent": "Recent projects",
    "home.quality": "Video quality", "home.advanced": "Advanced settings",
    "home.linkReading": "Reading link…", "home.linkReady": "Link ready", "home.linkFail": "Could not read link",
    "home.localReady": "Local file ready",
    "projects.title": "Projects", "projects.export": "Export combined", "projects.empty": "No projects yet. Create one from Home.",
    "projects.deleteConfirm": "Delete this project and all its clips?",
    "clips.deleteConfirm": "Delete this clip? Its rendered file is removed too.",
    "clips.deleted": "Clip deleted.",
    "editor.timeline": "Timeline", "editor.addText": "Add text", "editor.addMedia": "Add media", "editor.addMusic": "Add music",
    "editor.template": "Text template", "editor.previewDraft": "Quick preview", "editor.deleteItem": "Delete item",
    "timeline.video": "Video", "timeline.media": "Media", "timeline.text": "Text", "timeline.audio": "Audio",
    "voice.title": "Voice",
    "voice.lead": "Generate Indonesian or English voiceover with Piper (ultra light), or clone your own voice with Chatterbox.",
    "voice.tts": "Text to speech", "voice.text": "Text", "voice.lang": "Language", "voice.model": "Voice model",
    "voice.generate": "Generate voice", "voice.clone": "Voice cloning",
    "voice.cloneNote": "Only clone your own voice or voices you have permission to use. Outputs carry the PerTh watermark.",
    "voice.sample": "Reference recording (wav/mp3, 10-30 s)", "voice.cloneRun": "Clone", "voice.result": "Result",
    "models.title": "Models",
    "models.lead": "Models are not bundled. Studio ZAI detects your device and recommends the lightest matching models.",
    "models.download": "Download", "models.remove": "Remove", "models.installed": "installed", "models.pip": "via pip",
    "models.recommended": "recommended",
    "models.kindAsr": "Transcription", "models.kindTts": "Voice", "models.kindClone": "Voice cloning",
    "settings.title": "Settings", "settings.lang": "Interface language", "settings.asr": "Default transcription model",
    "settings.tts": "Default Indonesian voice", "settings.clone": "Default cloning model", "settings.crop": "Default crop mode",
    "settings.cookies": "cookies.txt (optional, for private videos)",
    "settings.llm": "Local LLM (optional)", "settings.llmNote": "For smarter moment picking. Ollama example: http://127.0.0.1:11434/v1",
    "settings.consent": "I only clone my own voice or voices I have permission to use.",
    "settings.openData": "Open data folder",
    "editor.trim": "Trim (seconds)", "editor.crop": "Framing", "editor.subtitleStyle": "Subtitle style",
    "editor.captions": "Captions (start|end|text per line)", "editor.audio": "Audio",
    "editor.narration": "Narration text for this clip", "editor.ttsClip": "Generate voice", "editor.cloneClip": "Clone for clip",
    "audio.original": "Original audio", "audio.voice": "Narration only", "audio.mix": "Narration + original",
    "toast.done": "Done", "toast.error": "Something went wrong", "toast.saved": "Saved",
  },
};

const state = {
  lang: localStorage.getItem("studiozai.lang") || "id",
  settings: {},
  voices: { piper: [], clone: [], available: {} },
  project: null,
  jobId: null,
  source: null,
};

const t = (key) => (I18N[state.lang] && I18N[state.lang][key]) || I18N.id[key] || key;
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

function applyI18n() {
  $$("[data-i18n]").forEach((el) => {
    el.textContent = t(el.dataset.i18n);
  });
  document.documentElement.lang = state.lang;
  $$("#langSeg button").forEach((button) => {
    button.classList.toggle("active", button.dataset.lang === state.lang);
  });
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch { /* keep status text */ }
    throw new Error(detail);
  }
  return response.status === 204 ? null : response.json();
}

function toast(message, type = "") {
  const node = document.createElement("div");
  node.className = `toast ${type}`;
  node.textContent = message;
  $("#toast").appendChild(node);
  setTimeout(() => node.remove(), type === "error" ? 9000 : 4500);
}

function mediaUrl(path) {
  return `/api/media?path=${encodeURIComponent(path)}`;
}

function fileName(path) {
  return (path || "").split(/[\\/]/).pop();
}

function formatClock(seconds) {
  const total = Math.max(0, Math.round(seconds || 0));
  const minutes = Math.floor(total / 60);
  const rest = total % 60;
  return `${minutes}:${String(rest).padStart(2, "0")}`;
}

/* ------------------------------------------------------------------ jobs */

let jobTimer = null;
let jobStartedAt = 0;

function fmtElapsed(seconds) {
  const total = Math.max(0, Math.floor(seconds));
  const m = Math.floor(total / 60);
  const s = String(total % 60).padStart(2, "0");
  return `${m}:${s}`;
}

let displayedProgress = 0;

function showProcessing(title) {
  displayedProgress = 0;
  const card = $("#processingCard");
  if (card) {
    card.classList.add("visible");
    $("#procTitle").textContent = title || t("common.processing");
    $("#procStage").textContent = t("common.processing");
    const fill = $("#procFill");
    fill.style.width = "2%";
    fill.classList.add("indeterminate");
    $("#procElapsed").textContent = "0:00";
  }
  const titleEl = $("#jobTitle");
  if (titleEl) titleEl.textContent = title || t("common.processing");
  jobStartedAt = Date.now();
  clearInterval(jobTimer);
  const tick = () => {
    const label = fmtElapsed((Date.now() - jobStartedAt) / 1000);
    const pe = $("#procElapsed");
    if (pe) pe.textContent = label;
    const je = $("#jobElapsed");
    if (je) je.textContent = label;
  };
  tick();
  jobTimer = setInterval(tick, 1000);
}

function hideProcessing() {
  const card = $("#processingCard");
  if (card) card.classList.remove("visible");
  clearInterval(jobTimer);
  jobTimer = null;
}

function trackJob(job) {
  if (!job || !job.id) return;
  state.jobId = job.id;
  const startBtn = $("#startBtn");
  if (startBtn) { startBtn.disabled = true; startBtn.textContent = t("common.processing") + "…"; }
  const jobbar = $("#jobbar");
  if (jobbar) jobbar.classList.add("visible");
  const jt = $("#jobTitle");
  if (jt) jt.textContent = job.title || t("common.processing");
  const js = $("#jobStage");
  if (js) js.textContent = t("common.processing");
  const jf = $("#jobFill");
  if (jf) jf.style.width = "2%";
  const jp = $("#jobPercent");
  if (jp) jp.textContent = "0%";
  showProcessing(job.title);

  const source = new EventSource(`/api/jobs/${job.id}/events`);
  source.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // Progress MONOTON: angka yang tampil tidak pernah mundur. Backend
    // melaporkan per-tahap (unduh 3-35%, transkrip 45-75%, dst) sehingga
    // tanpa clamp, bar akan "melompat mundur" tiap ganti tahap.
    const raw = Math.round(data.progress || 0);
    const percent = Math.max(displayedProgress, Math.min(100, raw));
    displayedProgress = percent;
    // Indeterminate hanya saat belum ada angka nyata (mis. unduh model pertama).
    const fill = $("#procFill");
    if (fill) {
      if (percent > 2) fill.classList.remove("indeterminate");
      fill.style.width = `${Math.max(2, percent)}%`;
    }
    const bar = $("#jobFill");
    if (bar) bar.style.width = `${percent}%`;
    const pct = $("#jobPercent");
    if (pct) pct.textContent = `${percent}%`;
    if (data.type === "progress") {
      const stageText = data.stage ? `${data.stage} — ${data.message || ""}` : (data.message || "");
      const stageEl = $("#jobStage");
      if (stageEl) stageText && (stageEl.textContent = stageText);
      const ps = $("#procStage");
      if (ps) ps.textContent = data.stage || t("common.processing");
      const pt = $("#procTitle");
      if (pt) pt.textContent = data.message || job.title || t("common.processing");
      const titleEl = $("#jobTitle");
      if (titleEl && data.message) titleEl.textContent = data.message;
      return;
    }
    if (data.type === "end") {
      source.close();
      const bar2 = $("#jobbar");
      if (bar2) bar2.classList.remove("visible");
      state.jobId = null;
      hideProcessing();
      if (startBtn) { startBtn.disabled = false; startBtn.textContent = t("home.start"); }
      if (data.status === "error") toast(data.error || t("toast.error"), "error");
      else toast(`${t("toast.done")}: ${data.title || ""}`);
      refreshAll();
      if (data.result && data.result.path) playAudio(data.result.path);
    }
  };
  source.onerror = () => {
    source.close();
    const bar3 = $("#jobbar");
    if (bar3) bar3.classList.remove("visible");
    hideProcessing();
    if (startBtn) { startBtn.disabled = false; startBtn.textContent = t("home.start"); }
    state.jobId = null;
  };
}

function playAudio(path) {
  state.source = path;
  $("#voiceResultCard").style.display = "block";
  $("#voicePlayer").src = mediaUrl(path);
  $("#voicePlayer").play().catch(() => {});
}

/* ------------------------------------------------------------------ nav */

function setPage(name) {
  $$(".page").forEach((page) => page.classList.toggle("active", page.id === `page-${name}`));
  $$("#nav button").forEach((button) => button.classList.toggle("active", button.dataset.page === name));
  if (name === "projects") renderProjects();
  if (name === "models") renderModels();
  if (name === "settings") renderSettings();
  if (name === "voice") renderVoice();
}

/* ------------------------------------------------------------------ home */

let linkInfoTimer = null;
let linkInfoCache = null;

function humanMB(bytes) {
  if (!bytes) return "?";
  const mb = bytes / 1024 / 1024;
  return mb >= 1024 ? `${(mb / 1024).toFixed(1)} GB` : `${mb.toFixed(0)} MB`;
}

function fmtDuration(seconds) {
  const total = Math.round(seconds || 0);
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  return h ? `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}` : `${m}:${String(s).padStart(2, "0")}`;
}

function showLinkPreview(info) {
  const wrap = $("#linkPreviewWrap");
  const box = $("#linkPreview");
  const qwrap = $("#qualityWrap");
  wrap.style.display = "flex";
  qwrap.style.display = "block";
  linkInfoCache = info;
  // Track audio multi-bahasa (video YouTube dengan dub resmi): tampilkan pilihan
  // hanya kalau memang ada lebih dari satu track.
  const tracks = info.audio_tracks || [];
  const trackWrap = $("#audioTrackWrap");
  const trackSelect = $("#audioTrack");
  if (trackWrap && trackSelect) {
    if (tracks.length > 1) {
      trackSelect.innerHTML = tracks
        .map((t) => `<option value="${t.lang || t.format_id}">${t.label || t.lang}</option>`)
        .join("");
      trackWrap.style.display = "block";
      const hintEl = $("#audioTrackHint");
      if (hintEl) hintEl.textContent = `${tracks.length} track audio terdeteksi — pilih bahasa yang dipakai klip.`;
    } else {
      trackWrap.style.display = "none";
      trackSelect.innerHTML = "";
    }
  }
  const hint = $("#qualityHint");
  const best = (info.formats || []).filter((f) => f.has_video);
  const perSize = {};
  for (const f of best) {
    const key = f.height >= 2160 ? "best" : f.height >= 1080 ? "1080p" : f.height >= 720 ? "720p" : "480p";
    if (!perSize[key] || (f.filesize && f.filesize > perSize[key])) perSize[key] = f.filesize || 0;
  }
  const order = ["best", "1080p", "720p", "480p"];
  hint.textContent = order
    .filter((k) => perSize[k])
    .map((k) => `${k} ≈ ${humanMB(perSize[k])}`)
    .join("  ·  ") || `${info.title} · ${fmtDuration(info.duration)}`;
  box.innerHTML = `
    <div class="row settings">
      <div style="display:grid;gap:2px;min-width:0">
        <span style="font-weight:600"><svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px;vertical-align:-2px"><path d="M20 6 9 17l-5-5"/></svg> ${t("home.linkReady")}</span>
        <span class="muted">${info.title} · ${fmtDuration(info.duration)}${info.uploader ? " · " + info.uploader : ""}</span>
      </div>
    </div>`;
}

function showLinkError(message) {
  const wrap = $("#linkPreviewWrap");
  const box = $("#linkPreview");
  wrap.style.display = "flex";
  $("#qualityWrap").style.display = "none";
  linkInfoCache = null;
  box.innerHTML = `<span class="muted"><svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" style="width:14px;height:14px;vertical-align:-2px"><circle cx="12" cy="12" r="9"/><path d="M12 8v4M12 16h.01"/></svg> ${t("home.linkFail")}: ${message}</span>`;
}

function hideLinkPreview() {
  $("#linkPreviewWrap").style.display = "none";
  $("#qualityWrap").style.display = "none";
  linkInfoCache = null;
}

function onSourceChanged() {
  const value = $("#source").value.trim();
  clearTimeout(linkInfoTimer);
  if (!value) { hideLinkPreview(); return; }
  const isUrl = /^https?:\/\//i.test(value);
  if (!isUrl) {
    // berkas lokal: tampilkan siap langsung
    const wrap = $("#linkPreviewWrap");
    const box = $("#linkPreview");
    wrap.style.display = "flex";
    $("#qualityWrap").style.display = "none";
    linkInfoCache = null;
    box.innerHTML = `<span class="muted"><svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px;vertical-align:-2px"><path d="M20 6 9 17l-5-5"/></svg> ${t("home.localReady")}: ${fileName(value)}</span>`;
    return;
  }
  // debounce 800ms supaya tidak request tiap ketikan
  const wrap = $("#linkPreviewWrap");
  const box = $("#linkPreview");
  wrap.style.display = "flex";
  box.innerHTML = `<span class="muted">… ${t("home.linkReading")}</span>`;
  linkInfoTimer = setTimeout(async () => {
    try {
      const info = await api("/api/link-info", { method: "POST", body: JSON.stringify({ url: value }) });
      showLinkPreview(info);
    } catch (error) {
      showLinkError(error.message);
    }
  }, 800);
}

async function startClipping() {
  const source = $("#source").value.trim();
  if (!source) {
    toast(t("home.source"), "error");
    return;
  }
  try {
    const project = await api("/api/projects", {
      method: "POST",
      body: JSON.stringify({ title: fileName(source) || "proyek", source: "", lang: $("#lang").value }),
    });
    const job = await api(`/api/projects/${project.id}/process`, {
      method: "POST",
      body: JSON.stringify({
        source,
        count: Number($("#count").value) || 5,
        min_len: Number($("#minLen").value) || 15,
        max_len: Number($("#maxLen").value) || 60,
        use_transcript: $("#useTranscript").checked,
        use_llm: $("#useLlm").checked,
        quality: $("#quality").value || "720p",
        subtitle_position: ($("#subPos") || {}).value || "bottom",
        canvas: ($("#canvasSize") || {}).value || "portrait",
        audio_mode: ($("#audioMode") || {}).value || "original",
        audio_lang: (($("#audioTrack") || {}).value || "") || null,
      }),
    });
    trackJob(job);
  } catch (error) {
    toast(error.message, "error");
  }
}

async function showDoctor() {
  try {
    const report = await api("/api/doctor");
    const hardware = report.hardware;
    const lines = [
      `Studio ZAI ${report.version}`,
      `${hardware.os} / ${hardware.arch} · Python ${hardware.python}`,
      `RAM ${hardware.ram_gb ?? "?"} GB · CPU ${hardware.cpu_count} core`,
      `GPU ${hardware.gpu && hardware.gpu.name ? hardware.gpu.name : "-"} · Encoder ${report.encoder}`,
      `Rekomendasi: ${report.tier.asr}, ${report.tier.tts}${report.tier.clone ? ", " + report.tier.clone : ""}`,
      ...report.tier.reasons.map((r) => `  · ${r}`),
    ];
    if (report.problems.length) lines.push("", ...report.problems.map((p) => `! ${p}`));
    const out = $("#doctorOut");
    out.style.display = "block";
    out.textContent = lines.join("\n");
  } catch (error) {
    toast(error.message, "error");
  }
}

async function renderHomeProjects() {
  try {
    const projects = await api("/api/projects");
    const box = $("#homeProjects");
    if (!projects.length) {
      box.innerHTML = `<div class="empty">${t("projects.empty")}</div>`;
      return;
    }
    box.innerHTML = projects.slice(0, 6).map(projectCard).join("");
    box.querySelectorAll("[data-project]").forEach((node) =>
      node.addEventListener("click", () => openProject(node.dataset.project))
    );
  } catch (error) {
    toast(error.message, "error");
  }
}

function projectCard(project) {
  const thumb = project.thumb ? `<img class="thumb" src="${mediaUrl(project.thumb)}" alt="" />` : `<div class="thumb"></div>`;
  return `<article class="clip" data-project="${project.id}" style="cursor:pointer">
    ${thumb}
    <div class="meta">
      <strong>${project.title}</strong>
      <span class="score">${project.clips} klip · ${project.duration_label || formatClock(project.duration)} · ${project.language || ""}</span>
    </div>
  </article>`;
}

/* ------------------------------------------------------------------ projects */

async function renderProjects() {
  if (state.project) return renderProjectDetail();
  try {
    const projects = await api("/api/projects");
    $("#projectDetail").style.display = "none";
    const list = $("#projectList");
    if (!projects.length) {
      list.innerHTML = `<div class="empty">${t("projects.empty")}</div>`;
      return;
    }
    list.innerHTML = `<div class="card tight">${projects.map((project) => `
      <div class="row settings">
        <div style="display:grid;gap:2px;min-width:0">
          <span style="font-weight:600">${project.title}</span>
          <span class="muted">${project.clips} klip · ${project.duration_label || ""} · ${new Date(project.updated * 1000).toLocaleDateString()}</span>
        </div>
        <div class="row" style="gap:var(--s2)">
          <button class="mini" data-open="${project.id}">${t("common.edit")}</button>
          <button class="mini" data-delete="${project.id}">${t("common.delete")}</button>
        </div>
      </div>`).join("")}</div>`;
    list.querySelectorAll("[data-open]").forEach((node) => node.addEventListener("click", () => openProject(node.dataset.open)));
    list.querySelectorAll("[data-delete]").forEach((node) =>
      node.addEventListener("click", async () => {
        if (!window.confirm(t("projects.deleteConfirm"))) return;
        try {
          await api(`/api/projects/${node.dataset.delete}`, { method: "DELETE" });
          renderProjects();
          toast(t("toast.done"), "ok");
        } catch (error) {
          toast(error.message, "error");
        }
      })
    );
  } catch (error) {
    toast(error.message, "error");
  }
}

async function openProject(projectId) {
  state.project = await api(`/api/projects/${projectId}`);
  setPage("projects");
  renderProjectDetail();
}

function renderProjectDetail() {
  const project = state.project;
  if (!project) return;
  $("#projectList").innerHTML = "";
  $("#projectDetail").style.display = "block";
  $("#detailTitle").textContent = project.title;
  $("#detailMeta").textContent = `${project.clips.length} klip · ${formatClock(project.duration)} · ${project.language || ""}`;
  const grid = $("#clipGrid");
  if (!project.clips.length) {
    grid.innerHTML = `<div class="empty">${t("projects.empty")}</div>`;
    return;
  }
  grid.innerHTML = project.clips.map((clip) => {
    const thumb = clip.files && clip.files.thumb
      ? `<img class="thumb" src="${mediaUrl(clip.files.thumb)}" alt="" loading="lazy" />`
      : `<div class="thumb skeleton"></div>`;
    const ready = Boolean(clip.files && clip.files.mp4);
    const status = ready ? `<span class="badge ok">siap</span>` : `<span class="badge warn">draft</span>`;
    return `<article class="clip">
      ${thumb}
      <div class="meta">
        <strong>${clip.title || "Klip " + (clip.index + 1)}</strong>
        <span class="score">${formatClock(clip.start)}–${formatClock(clip.end)} · skor ${(clip.score || 0).toFixed(2)}</span>
        <span>${status} <span class="badge">${clip.crop}</span></span>
      </div>
      <div class="actions">
        <button class="icon-btn" data-preview="${clip.index}" ${ready ? "" : "disabled style='opacity:.4'"}><svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>${t("common.preview")}</button>
        <button class="icon-btn" data-edit="${clip.index}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/></svg>${t("common.edit")}</button>
        <button class="icon-btn" data-render="${clip.index}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-3-6.7M21 3v6h-6"/></svg>${t("common.render")}</button>
        <button class="icon-btn" data-remove="${clip.index}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 6h18M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2m2 0v14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V6"/></svg>${t("common.delete")}</button>
      </div>
    </article>`;
  }).join("");

  grid.querySelectorAll("[data-edit]").forEach((node) => node.addEventListener("click", () => openEditor(Number(node.dataset.edit))));
  grid.querySelectorAll("[data-render]").forEach((node) =>
    node.addEventListener("click", async () => {
      const job = await api(`/api/projects/${project.id}/clips/${node.dataset.render}/render`, { method: "POST" });
      trackJob(job);
    })
  );
  grid.querySelectorAll("[data-remove]").forEach((node) =>
    node.addEventListener("click", async () => {
      if (!window.confirm(t("clips.deleteConfirm"))) return;
      try {
        await api(`/api/projects/${project.id}/clips/${node.dataset.remove}`, { method: "DELETE" });
        state.project = await api(`/api/projects/${project.id}`);
        renderProjectDetail();
        toast(t("clips.deleted"), "ok");
      } catch (error) {
        toast(error.message, "error");
      }
    })
  );
  grid.querySelectorAll("[data-preview]").forEach((node) =>
    node.addEventListener("click", () => {
      const clip = state.project.clips.find((c) => c.index === Number(node.dataset.preview));
      if (!clip || !clip.files || !clip.files.mp4) return toast(t("common.render"), "error");
      const track = clip.files.vtt ? `<track kind="subtitles" srclang="id" src="${mediaUrl(clip.files.vtt)}" default />` : "";
      openPanel(`
        <div class="spread"><h3>${clip.title || "Klip"}</h3><button class="mini" data-close>${t("common.close")}</button></div>
        <video controls autoplay src="${mediaUrl(clip.files.mp4)}">${track}</video>
        <p class="muted">${mediaUrl(clip.files.mp4)}</p>`);
    })
  );
}

/* ------------------------------------------------------------------ editor */

function captionsToText(captions) {
  return (captions || []).map((c) => `${c.start.toFixed(2)}|${c.end.toFixed(2)}|${c.text}`).join("\n");
}

function textToCaptions(text) {
  return text.split("\n").map((line) => line.trim()).filter(Boolean).map((line) => {
    const [start, end, ...rest] = line.split("|");
    return { start: Number(start) || 0, end: Number(end) || 0, text: rest.join("|").trim() };
  }).filter((c) => c.text);
}

/** Buka editor timeline (lihat timeline.js). */
function openEditor(index) {
  StudioTimeline.open(index);
}

function openPanel(html) {
  const panel = $("#editPanel");
  panel.innerHTML = html;
  panel.classList.add("open");
  panel.querySelectorAll("[data-close]").forEach((node) => node.addEventListener("click", closePanel));
}

function closePanel() {
  $("#editPanel").classList.remove("open");
}

/* ------------------------------------------------------------------ voice */

function voiceLabel(id) {
  const fake = { id, size_mb: null, note: "", langs: [] };
  if (id.includes("id_ID")) fake.langs = ["id"];
  else if (id.includes("en_")) fake.langs = ["en"];
  return modelName(fake);
}

function renderVoice() {
  const select = $("#ttsVoice");
  const available = state.voices.piper || [];
  select.innerHTML = available.map((id) => `<option value="${id}">${voiceLabel(id)}</option>`).join("");
  select.disabled = available.length === 0;
  const ttsBtn = $("#ttsBtn");
  if (ttsBtn) {
    ttsBtn.disabled = available.length === 0;
    ttsBtn.title = available.length === 0 ? "Unduh dulu model suara di halaman Model" : "";
  }
  if (available.length === 0) {
    select.innerHTML = `<option value="">— belum ada model suara —</option>`;
  }
  const hint = $("#cloneHint");
  if (!state.voices.available || !state.voices.available.chatterbox) {
    hint.textContent = "Chatterbox belum terpasang (pip install -e \"core[clone]\") — kloning nonaktif.";
  } else if (!state.settings.clone_consent) {
    hint.textContent = t("settings.consent");
  } else {
    hint.textContent = "";
  }
}

async function runTts() {
  const text = $("#ttsText").value.trim();
  if (!text) return toast(t("voice.text"), "error");
  const job = await api("/api/tts", {
    method: "POST",
    body: JSON.stringify({ text, lang: $("#ttsLang").value, voice_id: $("#ttsVoice").value || null }),
  });
  trackJob(job);
}

async function runClone() {
  const text = $("#cloneText").value.trim();
  const sample = $("#cloneSample").value.trim();
  if (!text || !sample) return toast(t("voice.sample"), "error");
  state.settings.clone_sample = sample;
  const job = await api("/api/clone", {
    method: "POST",
    body: JSON.stringify({ text, sample, lang: $("#cloneLang").value }),
  });
  trackJob(job);
}

/* ------------------------------------------------------------------ models */

/* Nama tampilan natural untuk id teknis model (tanpa underscore/dash = no AI slop) */
function modelName(model) {
  const id = model.id || "";
  const size = model.size_mb ? ` · ${model.size_mb} MB` : "";
  if (id.startsWith("whisper-")) {
    const tierName = id.replace("whisper-", "").replace("-int8", "");
    const label = { tiny: "Tiny", base: "Base", small: "Small", medium: "Medium" }[tierName] || tierName;
    const rec = /indonesia/i.test(model.note || "") ? ` · ${t("models.recommended")}` : "";
    return `Whisper ${label}${rec}${size ? ` — ${model.size_mb} MB` : ""}`;
  }
  if (id.startsWith("piper-")) {
    const lang = (model.langs || [])[0] === "id" ? "Indonesia" : (model.langs || [])[0] === "en" ? "English" : "";
    const voice = id.includes("news_tts") ? "News" : id.includes("lessac") ? "Lessac" : id.includes("alba") ? "Alba" : "";
    return `Suara ${lang}${voice ? ` ${voice}` : ""} — ${model.size_mb ?? "?"} MB`;
  }
  if (id === "chatterbox-base") return `Kloning Suara EN — ${model.size_mb ?? "?"} MB`;
  if (id === "chatterbox-id-finetune") return `Kloning Suara Indonesia — ${model.size_mb ?? "?"} MB`;
  if (id === "zipvoice-zh-en") return `Kloning Ringan EN — ${model.size_mb ?? "?"} MB`;
  if (id === "chatterbox-gguf-q4") return `Kloning Eksperimental — ${model.size_mb ?? "?"} MB`;
  if (id === "mms-tts-ind") return `Suara Indonesia Alternatif — ${model.size_mb ?? "?"} MB`;
  return `${id}${size}`;
}

function kindName(kind) {
  return kind === "asr" ? t("models.kindAsr") : kind === "tts" ? t("models.kindTts") : t("models.kindClone");
}

async function renderModels() {
  try {
    const data = await api("/api/models");
    const hardware = data.hardware;
    const tier = data.tier;
    const asrRec = (data.models || []).find((m) => m.id === tier.asr);
    const ttsRec = (data.models || []).find((m) => m.id === tier.tts);
    $("#hardwareCard").innerHTML = `
      <div class="row settings" style="border-bottom:1px solid var(--separator)">
        <span style="font-weight:600">${hardware.os} / ${hardware.arch}</span>
        <span class="muted">Python ${hardware.python}</span>
      </div>
      <div class="row settings">
        <span class="muted">RAM ${hardware.ram_gb ?? "?"} GB · CPU ${hardware.cpu_count} core · GPU ${(hardware.gpu && hardware.gpu.name) || "—"} · Disk ${hardware.disk_free_gb} GB</span>
      </div>
      <div class="row settings" style="border-bottom:0">
        <span class="muted">${tier.reasons.join(" · ")}</span>
      </div>
      <div class="row" style="gap:var(--s2);margin-top:var(--s3)">
        ${asrRec ? `<span class="badge info">${modelName(asrRec)}</span>` : ""}
        ${ttsRec ? `<span class="badge info">${modelName(ttsRec)}</span>` : ""}
      </div>`;
    $("#modelList").innerHTML = data.models.map((model) => `
      <div class="card tight">
        <div class="row settings">
          <div style="display:grid;gap:2px;min-width:0">
            <span style="font-weight:600">${modelName(model)}</span>
            <span class="muted">${kindName(model.kind)}${model.note ? " · " + model.note : ""}</span>
          </div>
          <div class="row" style="gap:var(--s2)">
            ${model.installed ? `<span class="badge ok">${t("models.installed")}</span>` : (model.requires_pip ? `<span class="badge">${t("models.pip")}</span>` : "")}
            ${model.installed ? `<button class="mini" data-remove-model="${model.id}">${t("models.remove")}</button>`
    : `<button class="primary" data-download="${model.id}">${t("models.download")}</button>`}
          </div>
        </div>
      </div>`).join("");
    $$("[data-download]").forEach((node) =>
      node.addEventListener("click", async () => {
        const job = await api(`/api/models/${node.dataset.download}/download`, { method: "POST" });
        trackJob(job);
      })
    );
    $$("[data-remove-model]").forEach((node) =>
      node.addEventListener("click", async () => {
        await api(`/api/models/${node.dataset.removeModel}`, { method: "DELETE" });
        renderModels();
      })
    );
  } catch (error) {
    toast(error.message, "error");
  }
}

/* ------------------------------------------------------------------ settings */

async function renderSettings() {
  if (!state.voices.piper) await loadVoices();
  const settings = state.settings;
  $("#setLang").value = state.lang;
  const asrIds = ["whisper-tiny-int8", "whisper-base-int8", "whisper-small-int8", "whisper-medium-int8"];
  $("#setAsr").innerHTML = asrIds
    .map((id) => `<option value="${id}" ${settings.asr_model === id ? "selected" : ""}>${voiceLabel(id)}</option>`).join("");
  const ttsIds = state.voices.piper.filter((id) => id.includes("id_ID"));
  $("#setTts").innerHTML = (ttsIds.length ? ttsIds : [""]).map((id) => id
    ? `<option value="${id}" ${settings.tts_voice_id === id ? "selected" : ""}>${voiceLabel(id)}</option>`
    : `<option value="">— belum ada —</option>`).join("");
  const cloneIds = state.voices.clone || [];
  $("#setClone").innerHTML = (cloneIds.length ? cloneIds : [""]).map((id) => id
    ? `<option value="${id}" ${settings.clone_model === id ? "selected" : ""}>${voiceLabel(id)}</option>`
    : `<option value="">— belum ada —</option>`).join("");
  $("#setCrop").value = settings.crop || "center";
  $("#setCookies").value = settings.cookies_path || "";
  $("#setLlmUrl").value = settings.llm_base_url || "";
  $("#setLlmModel").value = settings.llm_model || "";
  $("#setLlmKey").value = settings.llm_api_key || "";
  $("#setConsent").checked = Boolean(settings.clone_consent);
}

async function saveSettings() {
  const values = {
    lang: $("#setLang").value,
    asr_model: $("#setAsr").value,
    tts_voice_id: $("#setTts").value,
    clone_model: $("#setClone").value,
    crop: $("#setCrop").value,
    cookies_path: $("#setCookies").value,
    llm_base_url: $("#setLlmUrl").value,
    llm_model: $("#setLlmModel").value,
    clone_consent: $("#setConsent").checked,
  };
  const key = $("#setLlmKey").value;
  if (key && key !== "***") values.llm_api_key = key;
  state.settings = await api("/api/settings", { method: "POST", body: JSON.stringify({ values }) });
  state.lang = values.lang;
  localStorage.setItem("studiozai.lang", state.lang);
  applyI18n();
  toast(t("toast.saved"));
}

function openDataFolder() {
  const path = state.settings.data_dir_path || "";
  if (window.pywebview && window.pywebview.api && path) window.pywebview.api.open_folder(path);
  else toast(state.settings.data_dir || "", "");
}

/* ------------------------------------------------------------------ wizard setup */

const wizard = { step: 0, device: null, models: [], chosen: [], busy: false };

function wizardShow(step) {
  wizard.step = step;
  const overlay = $("#wizardOverlay");
  const title = $("#wizardTitle");
  const sub = $("#wizardSub");
  const body = $("#wizardBody");
  const actions = $("#wizardActions");
  overlay.hidden = false;

  if (step === 0) {
    // Ganti checkbox mentah dengan toggle custom + ikon langkah.
    title.textContent = "Selamat datang di Studio ZAI";
    sub.textContent = "3 langkah cepat sampai siap dipakai — semua model jalan lokal di perangkatmu.";
    body.innerHTML = `
      <div class="wizard-body-row"><span class="dot">1</span><span class="label">Deteksi perangkat<span class="sub">RAM, CPU/GPU, ruang disk dicek otomatis</span></span></div>
      <div class="wizard-body-row"><span class="dot">2</span><span class="label">Pilih model<span class="sub">rekomendasi paling ringan sudah dicentang</span></span></div>
      <div class="wizard-body-row"><span class="dot">3</span><span class="label">Unduh sekali, pakai offline<span class="sub">progress per model terlihat jelas</span></span></div>`;
    actions.innerHTML = `
      <button class="primary" id="wzStart">Mulai setup</button>
      <button class="link" id="wzSkip">Nanti saja</button>`;
    $("#wzStart").addEventListener("click", () => wizardDetect());
    $("#wzSkip").addEventListener("click", wizardDone);
  }
}

async function wizardDetect() {
  const body = $("#wizardBody");
  const actions = $("#wizardActions");
  actions.innerHTML = "";
  body.innerHTML = `<div class="processing-head" style="justify-content:center"><div class="spinner"></div><span class="muted">Mendeteksi perangkat…</span></div>`;
  try {
    wizard.data = await api("/api/models");
    wizard.device = wizard.data.hardware;
    wizard.models = wizard.data.models;
    // Pilih otomatis model yang direkomendasikan perangkat ini.
    const tier = wizard.data.tier;
    const recommended = [tier.asr, tier.tts].filter(Boolean);
    wizard.chosen = recommended.slice();
    wizardShowRecommend();
  } catch (error) {
    body.innerHTML = `<p class="muted">Gagal mendeteksi: ${error.message}</p>`;
  }
}

function wizardShowRecommend() {
  const device = wizard.device;
  const tier = wizard.data.tier;
  $("#wizardTitle").textContent = "Perangkatmu terdeteksi";
  $("#wizardSub").textContent = `${device.os} · RAM ${device.ram_gb ?? "?"} GB · ${device.cpu_count} core · disk bebas ${device.disk_free_gb} GB`;

  const rows = wizard.models.map((model) => {
    const rec = wizard.chosen.includes(model.id);
    const markSvg = model.kind === "asr"
      ? '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:16px;height:16px;vertical-align:-3px"><rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/></svg>'
      : model.kind === "tts"
        ? '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:16px;height:16px;vertical-align:-3px"><path d="M11 5 6 9H3v6h3l5 4zM15.5 8.5a5 5 0 0 1 0 7M18.5 5.5a9 9 0 0 1 0 13"/></svg>'
        : '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:16px;height:16px;vertical-align:-3px"><path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M5.6 18.4l2.1-2.1M16.3 7.7l2.1-2.1"/></svg>';
    return `
    <label class="wizard-body-row" style="cursor:pointer">
      <input type="checkbox" data-model="${model.id}" ${rec ? "checked" : ""} ${model.installed ? "disabled" : ""} />
      <span class="label">
        ${markSvg} ${modelName(model)}
        <span class="sub">${model.note || ""}</span>
      </span>
      ${model.installed ? `<span class="stage-pill" style="background:rgba(48,209,88,.16);color:var(--green)"><svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" style="width:12px;height:12px"><path d="M20 6 9 17l-5-5"/></svg></span>` : ""}
    </label>`;
  }).join("");

  const recAsr = wizard.models.find((m) => m.id === tier.asr);
  const recTts = wizard.models.find((m) => m.id === tier.tts);
  $("#wizardBody").innerHTML = `
    <p class="muted" style="text-align:left;margin:0 0 var(--s3)">Rekomendasi untuk perangkatmu: <strong>${recAsr ? modelName(recAsr) : tier.asr}</strong> + <strong>${recTts ? modelName(recTts) : tier.tts}</strong></p>
    ${rows}`;
  $("#wizardActions").innerHTML = `
    <button class="primary" id="wzInstall">Unduh & pasang</button>
    <button class="link" id="wzLater">Lewati dulu</button>`;

  $("#wizardBody").querySelectorAll("[data-model]").forEach((cb) =>
    cb.addEventListener("change", () => {
      const id = cb.dataset.model;
      if (cb.checked && !wizard.chosen.includes(id)) wizard.chosen.push(id);
      if (!cb.checked) wizard.chosen = wizard.chosen.filter((x) => x !== id);
    })
  );
  $("#wzInstall").addEventListener("click", wizardInstall);
  $("#wzLater").addEventListener("click", wizardDone);
}

async function wizardInstall() {
  if (wizard.busy) return;
  wizard.busy = true;
  const toInstall = wizard.chosen.filter((id) => {
    const model = wizard.models.find((m) => m.id === id);
    return model && !model.installed;
  });

  $("#wizardTitle").textContent = "Memasang model";
  $("#wizardSub").textContent = "Tunggu sampai selesai. Ini hanya dilakukan sekali.";
  $("#wizardActions").innerHTML = "";

  const body = $("#wizardBody");
  body.innerHTML = toInstall.map((id) => {
    const model = wizard.models.find((m) => m.id === id);
    return `
    <div class="wizard-body-row" data-row="${id}">
      <span class="dot" data-dot="${id}">…</span>
      <span class="label">${model ? modelName(model) : id}
        <div class="wizard-progress"><span data-bar="${id}" style="width:0%"></span></div>
      </span>
      <span class="muted" data-pct="${id}">0%</span>
    </div>`;
  }).join("");

  for (const id of toInstall) {
    await wizardDownloadModel(id);
  }
  wizard.busy = false;
  wizardFinish();
}

function wizardDownloadModel(id) {
  return new Promise((resolve) => {
    const dot = document.querySelector(`[data-dot="${id}"]`);
    const bar = document.querySelector(`[data-bar="${id}"]`);
    const pct = document.querySelector(`[data-pct="${id}"]`);
    if (dot) dot.classList.add("run");
    let shown = 0;

    api(`/api/models/${id}/download`, { method: "POST" }).then((job) => {
      const source = new EventSource(`/api/jobs/${job.id}/events`);
      // Tampilkan nilai TERTINGGI yang pernah terlihat (monoton) supaya
      // bar wizard tidak ikut "mundur" saat backend ganti tahap.
      source.onmessage = (event) => {
        const data = JSON.parse(event.data);
        const progress = Math.max(shown, Math.round(data.progress || 0));
        shown = progress;
        if (bar) bar.style.width = `${progress}%`;
        if (pct) pct.textContent = `${progress}%`;
        if (data.type === "end") {
          source.close();
          if (data.status === "error") {
            if (dot) dot.classList.remove("run");
            if (pct) pct.textContent = "gagal";
            if (bar) bar.style.background = "var(--red)";
          } else {
            if (dot) { dot.classList.remove("run"); dot.classList.add("ok"); dot.innerHTML = '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" style="width:13px;height:13px"><path d="M20 6 9 17l-5-5"/></svg>'; }
            if (bar) bar.style.width = "100%";
            if (pct) pct.textContent = "100%";
          }
          resolve();
        }
      };
      source.onerror = () => { source.close(); resolve(); };
    }).catch(() => resolve());
  });
}

async function wizardFinish() {
  $("#wizardTitle").textContent = "Siap dipakai";
  $("#wizardSub").textContent = "Model terpasang. Semua fitur inti jalan lokal dan offline.";
  $("#wizardBody").innerHTML = "";
  $("#wizardActions").innerHTML = `<button class="primary" id="wzGo">Mulai pakai</button>`;
  $("#wzGo").addEventListener("click", wizardDone);
  await refreshAll();
}

async function wizardDone() {
  $("#wizardOverlay").hidden = true;
  await api("/api/settings", { method: "POST", body: JSON.stringify({ values: { setup_done: true } }) }).catch(() => {});
}

async function checkWizard() {
  try {
    const settings = await api("/api/settings");
    const models = await api("/api/models");
    // "Lengkap" = minimal 1 ASR + 1 TTS terpasang (syarat klip + subtitle + suara jalan).
    const installed = (models.models || []).filter((m) => m.installed).map((m) => m.kind);
    const coreReady = installed.includes("asr") && installed.includes("tts");

    // Wizard layar penuh HANYA saat pertama kali (belum pernah selesai setup).
    // Sebelumnya wizard muncul terus selama model belum lengkap, sehingga
    // seluruh UI tampak kusam/terhalang overlay setiap dibuka.
    if (!settings.setup_done) {
      wizardShow(0);
      return;
    }

    // Model belum lengkap setelah setup -> cukup banner kecil di Beranda.
    const banner = $("#modelBanner");
    if (coreReady) {
      if (banner) banner.remove();
      return;
    }
    if (banner) return;
    const home = $("#page-home");
    if (!home) return;
    const node = document.createElement("div");
    node.id = "modelBanner";
    node.className = "card tight";
    node.innerHTML = `
      <div class="row settings">
        <div>
          <span data-i18n="models.need">Model belum lengkap</span>
          <span class="sub">Unduh model transkripsi + suara sekali saja, lalu semua jalan offline.</span>
        </div>
        <div class="row" style="gap:8px">
          <button class="mini" id="bannerSetup">Siapkan</button>
          <button class="mini" id="bannerHide">Nanti</button>
        </div>
      </div>`;
    home.insertBefore(node, home.children[1] || null);
    $("#bannerSetup").addEventListener("click", () => {
      node.remove();
      setPage("models");
    });
    $("#bannerHide").addEventListener("click", () => node.remove());
  } catch { /* abaikan saat pertama kali */ }
}

/* ------------------------------------------------------------------ boot */

async function loadVoices() {
  state.voices = await api("/api/voices");
}

async function refreshAll() {
  await renderHomeProjects();
  if ($("#page-projects").classList.contains("active")) {
    if (state.project) state.project = await api(`/api/projects/${state.project.id}`);
    renderProjects();
  }
  if ($("#page-models").classList.contains("active")) renderModels();
}

function pickFile(target) {
  if (window.pywebview && window.pywebview.api) {
    return window.pywebview.api.pick_file().then((path) => {
      if (path) { $(target).value = path; onSourceChanged(); }
    });
  }
  const input = document.createElement("input");
  input.type = "file";
  input.accept = "video/*,audio/*";
  input.onchange = () => {
    if (input.files[0]) { $(target).value = input.files[0].name; onSourceChanged(); }
  };
  input.click();
}

async function boot() {
  applyI18n();
  try {
    state.settings = await api("/api/settings");
    if (state.settings.lang && state.settings.lang !== state.lang) {
      state.lang = state.settings.lang;
      localStorage.setItem("studiozai.lang", state.lang);
      applyI18n();
    }
    const health = await api("/api/health");
    $("#versionHint").textContent = `v${health.version}`;
  } catch (error) {
    toast(error.message, "error");
  }
  await loadVoices();
  await renderHomeProjects();

  $("#nav").addEventListener("click", (event) => {
    const button = event.target.closest("button[data-page]");
    if (button) setPage(button.dataset.page);
  });
  $("#langSeg").addEventListener("click", (event) => {
    const button = event.target.closest("button[data-lang]");
    if (!button) return;
    state.lang = button.dataset.lang;
    localStorage.setItem("studiozai.lang", state.lang);
    applyI18n();
    refreshAll();
  });
  $("#startBtn").addEventListener("click", startClipping);
  $("#doctorBtn").addEventListener("click", showDoctor);
  // Wizard bisa dibuka kapan saja dari halaman Model (tidak hanya saat pertama kali).
  const wizardBtn = $("#openWizard");
  if (wizardBtn) wizardBtn.addEventListener("click", () => wizardShow(0));
  $("#source").addEventListener("input", onSourceChanged);
  $("#pickFile").addEventListener("click", () => pickFile("#source"));
  $("#pickSample").addEventListener("click", () => pickFile("#cloneSample"));
  $("#refreshProjects").addEventListener("click", () => { state.project = null; renderProjects(); });
  $("#backBtn").addEventListener("click", () => { state.project = null; renderProjects(); });
  $("#exportBtn").addEventListener("click", async () => {
    if (!state.project) return;
    const job = await api(`/api/projects/${state.project.id}/export`, { method: "POST" });
    trackJob(job);
  });
  $("#ttsBtn").addEventListener("click", runTts);
  $("#cloneBtn").addEventListener("click", runClone);
  $("#saveSettings").addEventListener("click", saveSettings);
  $("#openDataFolder").addEventListener("click", openDataFolder);
  $("#jobCancel").addEventListener("click", async () => {
    if (state.jobId) await api(`/api/jobs/${state.jobId}/cancel`, { method: "POST" });
  });
  $("#procCancel").addEventListener("click", async () => {
    if (state.jobId) await api(`/api/jobs/${state.jobId}/cancel`, { method: "POST" });
  });

  checkWizard();
}

boot();
