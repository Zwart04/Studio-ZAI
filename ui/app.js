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
    "projects.title": "Proyek", "projects.export": "Export gabungan", "projects.empty": "Belum ada proyek. Buat dari halaman Beranda.",
    "voice.title": "Suara otomatis",
    "voice.lead": "Buat voiceover Bahasa Indonesia atau Inggris dengan Piper (super ringan), atau kloning suaramu sendiri dengan Chatterbox.",
    "voice.tts": "Text to speech", "voice.text": "Teks", "voice.lang": "Bahasa", "voice.model": "Model suara",
    "voice.generate": "Buat suara", "voice.clone": "Kloning suara",
    "voice.cloneNote": "Gunakan hanya suara milikmu sendiri atau yang kamu punya izin. Output otomatis mengandung watermark PerTh.",
    "voice.sample": "Contoh rekaman (wav/mp3, 10-30 detik)", "voice.cloneRun": "Kloning", "voice.result": "Hasil",
    "models.title": "Model",
    "models.lead": "Model tidak dibundel dalam aplikasi. Studio ZAI mendeteksi perangkatmu dan menyarankan model paling ringan yang cocok.",
    "models.download": "Unduh", "models.remove": "Hapus", "models.installed": "terpasang", "models.pip": "via pip",
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
    "projects.title": "Projects", "projects.export": "Export combined", "projects.empty": "No projects yet. Create one from Home.",
    "voice.title": "Voice",
    "voice.lead": "Generate Indonesian or English voiceover with Piper (ultra light), or clone your own voice with Chatterbox.",
    "voice.tts": "Text to speech", "voice.text": "Text", "voice.lang": "Language", "voice.model": "Voice model",
    "voice.generate": "Generate voice", "voice.clone": "Voice cloning",
    "voice.cloneNote": "Only clone your own voice or voices you have permission to use. Outputs carry the PerTh watermark.",
    "voice.sample": "Reference recording (wav/mp3, 10-30 s)", "voice.cloneRun": "Clone", "voice.result": "Result",
    "models.title": "Models",
    "models.lead": "Models are not bundled. Studio ZAI detects your device and recommends the lightest matching models.",
    "models.download": "Download", "models.remove": "Remove", "models.installed": "installed", "models.pip": "via pip",
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

function trackJob(job) {
  if (!job || !job.id) return;
  state.jobId = job.id;
  $("#jobbar").classList.add("visible");
  $("#jobStage").textContent = job.title || "";
  $("#jobFill").style.width = "2%";
  $("#jobPercent").textContent = "0%";

  const source = new EventSource(`/api/jobs/${job.id}/events`);
  source.onmessage = (event) => {
    const data = JSON.parse(event.data);
    const percent = Math.round(data.progress || 0);
    $("#jobFill").style.width = `${percent}%`;
    $("#jobPercent").textContent = `${percent}%`;
    $("#jobStage").textContent = data.stage ? `${data.stage} — ${data.message || ""}` : (data.message || "");
    if (data.type === "end") {
      source.close();
      $("#jobbar").classList.remove("visible");
      state.jobId = null;
      if (data.status === "error") toast(data.error || t("toast.error"), "error");
      else toast(`${t("toast.done")}: ${data.title || ""}`);
      refreshAll();
      if (data.result && data.result.path) playAudio(data.result.path);
    }
  };
  source.onerror = () => {
    source.close();
    $("#jobbar").classList.remove("visible");
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
        await api(`/api/projects/${node.dataset.delete}`, { method: "DELETE" });
        renderProjects();
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
      ? `<img class="thumb" src="${mediaUrl(clip.files.thumb)}" alt="" />`
      : `<div class="thumb"></div>`;
    const status = clip.files && clip.files.mp4 ? `<span class="badge ok">siap</span>` : `<span class="badge warn">draft</span>`;
    return `<article class="clip">
      ${thumb}
      <div class="meta">
        <strong>${clip.title || "Klip " + (clip.index + 1)}</strong>
        <span class="score">${formatClock(clip.start)}–${formatClock(clip.end)} · skor ${(clip.score || 0).toFixed(2)}</span>
        <span>${status} <span class="badge">${clip.crop}</span></span>
      </div>
      <div class="actions">
        <button class="mini" data-preview="${clip.index}">${t("common.preview")}</button>
        <button class="mini" data-edit="${clip.index}">${t("common.edit")}</button>
        <button class="mini" data-render="${clip.index}">${t("common.render")}</button>
        <button class="mini" data-remove="${clip.index}">${t("common.delete")}</button>
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
      await api(`/api/projects/${project.id}/clips/${node.dataset.remove}`, { method: "DELETE" });
      state.project = await api(`/api/projects/${project.id}`);
      renderProjectDetail();
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

function openEditor(index) {
  const clip = state.project.clips.find((c) => c.index === index);
  if (!clip) return;
  openPanel(`
    <div class="spread"><h3>${clip.title || "Klip " + (index + 1)}</h3><button class="mini" data-close>${t("common.close")}</button></div>
    <div class="grid-2">
      <div><label>${t("editor.trim")} — mulai</label><input type="number" step="0.1" id="edStart" value="${clip.start}" /></div>
      <div><label>${t("editor.trim")} — selesai</label><input type="number" step="0.1" id="edEnd" value="${clip.end}" /></div>
      <div><label>${t("editor.crop")}</label>
        <select id="edCrop">
          <option value="center" ${clip.crop === "center" ? "selected" : ""}>Center 9:16</option>
          <option value="blur" ${clip.crop === "blur" ? "selected" : ""}>Blur background</option>
          <option value="none" ${clip.crop === "none" ? "selected" : ""}>Tanpa crop</option>
        </select>
      </div>
      <div><label>${t("editor.subtitleStyle")}</label>
        <select id="edPreset">
          <option value="clean" ${clip.subtitle_preset === "clean" ? "selected" : ""}>Clean</option>
          <option value="bold_highlight" ${clip.subtitle_preset === "bold_highlight" ? "selected" : ""}>Bold highlight</option>
        </select>
      </div>
      <div><label>${t("editor.audio")}</label>
        <select id="edAudio">
          <option value="original" ${clip.audio_mode === "original" ? "selected" : ""}>${t("audio.original")}</option>
          <option value="voice" ${clip.audio_mode === "voice" ? "selected" : ""}>${t("audio.voice")}</option>
          <option value="mix" ${clip.audio_mode === "mix" ? "selected" : ""}>${t("audio.mix")}</option>
        </select>
      </div>
      <div><label>Volume audio asli (0-1)</label><input type="number" step="0.05" min="0" max="1" id="edOrigVol" value="${clip.original_volume ?? 0.25}" /></div>
    </div>
    <label style="margin-top:16px">${t("editor.captions")}</label>
    <textarea id="edCaptions" rows="8">${captionsToText(clip.captions)}</textarea>
    <label style="margin-top:16px">${t("editor.narration")}</label>
    <textarea id="edNarration" rows="3" placeholder="Teks narasi…"></textarea>
    <div class="row" style="margin-top:12px">
      <button class="ghost" id="edTts">${t("editor.ttsClip")}</button>
      <button class="ghost" id="edClone">${t("editor.cloneClip")}</button>
    </div>
    <div class="row" style="margin-top:24px">
      <button class="primary" id="edSave">${t("common.save")}</button>
      <button class="ghost" id="edRender">${t("common.render")}</button>
    </div>`);

  $("#edSave").addEventListener("click", async () => {
    const payload = {
      start: Number($("#edStart").value),
      end: Number($("#edEnd").value),
      crop: $("#edCrop").value,
      subtitle_preset: $("#edPreset").value,
      audio_mode: $("#edAudio").value,
      original_volume: Number($("#edOrigVol").value),
      captions: textToCaptions($("#edCaptions").value),
    };
    await api(`/api/projects/${state.project.id}/clips/${index}`, { method: "PATCH", body: JSON.stringify(payload) });
    state.project = await api(`/api/projects/${state.project.id}`);
    toast(t("toast.saved"));
    renderProjectDetail();
  });

  $("#edRender").addEventListener("click", async () => {
    const job = await api(`/api/projects/${state.project.id}/clips/${index}/render`, { method: "POST" });
    trackJob(job);
    closePanel();
  });

  $("#edTts").addEventListener("click", async () => {
    const text = $("#edNarration").value.trim();
    if (!text) return toast(t("voice.text"), "error");
    const job = await api(`/api/projects/${state.project.id}/tts`, {
      method: "POST",
      body: JSON.stringify({ text, lang: state.project.language || "id", clip: index }),
    });
    trackJob(job);
    closePanel();
  });

  $("#edClone").addEventListener("click", async () => {
    const text = $("#edNarration").value.trim();
    const sample = state.settings.clone_sample || "";
    if (!text || !sample) return toast(t("voice.sample"), "error");
    const job = await api(`/api/projects/${state.project.id}/clone`, {
      method: "POST",
      body: JSON.stringify({ text, sample, lang: state.project.language || "id", clip: index }),
    });
    trackJob(job);
    closePanel();
  });
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

function renderVoice() {
  const select = $("#ttsVoice");
  select.innerHTML = (state.voices.piper || []).map((id) => `<option value="${id}">${id}</option>`).join("");
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

async function renderModels() {
  try {
    const data = await api("/api/models");
    const hardware = data.hardware;
    const tier = data.tier;
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
        <span class="badge info">${tier.asr}</span>
        <span class="badge info">${tier.tts}</span>
        ${tier.clone ? `<span class="badge info">${tier.clone}</span>` : ""}
      </div>`;
    $("#modelList").innerHTML = data.models.map((model) => `
      <div class="card tight">
        <div class="row settings">
          <div style="display:grid;gap:2px;min-width:0">
            <span style="font-weight:600">${model.id}</span>
            <span class="muted">${model.kind} · ${model.size_mb ?? "?"} MB · ${model.license}${model.note ? " · " + model.note : ""}</span>
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
  $("#setAsr").innerHTML = ["whisper-tiny-int8", "whisper-base-int8", "whisper-small-int8", "whisper-medium-int8"]
    .map((id) => `<option ${settings.asr_model === id ? "selected" : ""}>${id}</option>`).join("");
  $("#setTts").innerHTML = state.voices.piper.filter((id) => id.includes("id_ID"))
    .map((id) => `<option ${settings.tts_voice_id === id ? "selected" : ""}>${id}</option>`).join("");
  $("#setClone").innerHTML = state.voices.clone
    .map((id) => `<option ${settings.clone_model === id ? "selected" : ""}>${id}</option>`).join("");
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

async function pickFile(target) {
  if (window.pywebview && window.pywebview.api) {
    const path = await window.pywebview.api.pick_file();
    if (path) $(target).value = path;
    return;
  }
  const input = document.createElement("input");
  input.type = "file";
  input.accept = "video/*,audio/*";
  input.onchange = () => {
    if (input.files[0]) $(target).value = input.files[0].name;
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
}

boot();
