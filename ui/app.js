const I18N = {
  id: {
    "settings.asrDevice": "Perangkat ASR",
    "hybrid.localOnly": "Full Offline memerlukan berkas lokal, bukan link.",
    "project.relink": "Tautkan ulang video", "project.sourcePath": "Lokasi video asli setelah dipindah",
    "project.relinkHint": "Pilih video yang sama agar trim, subtitle, dan ekspor tetap sesuai.",
    "hybrid.mode": "Mode pemrosesan", "hybrid.offline": "Full Offline · berkas lokal", "hybrid.online": "Online AI · opsional",
    "hybrid.model": "Model LLM lokal terpasang", "hybrid.none": "Belum dipilih · fallback heuristik", "hybrid.detect": "Cari model lokal",
    "hybrid.hint": "Caption diprioritaskan. Model tidak diunduh otomatis.", "hybrid.searching": "Mencari model terpasang...",
    "hybrid.found": "{count} model runtime tersedia.", "hybrid.gguf": "Model GGUF di komputer", "hybrid.load": "Muat model GGUF",
    "hybrid.stop": "Lepaskan model dari RAM", "hybrid.select": "Pilih model", "hybrid.stopped": "Model dilepas dari RAM.",
    "nav.gallery": "Galeri klip", "gallery.lead": "Semua klip dari proyekmu, siap diputar, diedit, dan diunduh kembali.",
    "gallery.empty": "Belum ada klip. Mulai dari video panjang di Beranda.", "gallery.draft": "Belum dirender",
    "gallery.search": "Cari judul klip atau proyek", "gallery.all": "Semua klip", "gallery.ready": "Sudah dirender",
    "gallery.latest": "Terbaru", "gallery.score": "Skor tertinggi", "gallery.noMatch": "Tidak ada klip yang cocok.",
    "gallery.status": "Status", "gallery.order": "Urutkan", "gallery.missing": "Klip ini sudah dihapus. Muat ulang galeri.",
    "clips.score": "Skor momen", "clips.original": "Utama", "clips.download": "Unduh", "clips.select": "Pilih untuk ekspor",
    "batch.title": "Ekspor banyak klip", "batch.help": "Pilih klip dan format. Setiap hasil disimpan terpisah dan tersedia di galeri.",
    "batch.all": "Pilih semua", "batch.none": "Kosongkan pilihan", "batch.render": "Render pilihan", "batch.required": "Pilih minimal satu klip dan satu format.",
    "batch.limit": "Pilih maksimal 20 klip per batch.", "batch.summary": "{clips} klip × {formats} format = {total} video",
    "batch.busy": "Tunggu proses aktif selesai sebelum memulai render berikutnya.", "batch.done": "{total} video berhasil dibuat. Unduh dari kartu klip atau Galeri klip.",
    "common.processing": "Memproses",
    "editor.style": "Tipografi subtitle", "editor.trimHint": "Framing mengikuti rasio kanvas pilihanmu.", "editor.timelineHint": "Pilih blok untuk mengedit. Geser tepi untuk durasi. Video diperbarui otomatis.",
    "nav.home": "Beranda", "nav.projects": "Proyek", "nav.voice": "Suara", "nav.models": "Model", "nav.settings": "Pengaturan",
    "common.refresh": "Muat ulang", "common.back": "Kembali", "common.save": "Simpan", "common.cancel": "Batal",
    "common.delete": "Hapus", "common.render": "Render", "common.edit": "Edit", "common.close": "Tutup", "common.preview": "Pratinjau",
    "home.title": "Pilih momen. Susun klipmu.",
    "home.lead": "Tempel link atau pilih video. Klip 9:16 dan subtitle dibuat lokal di perangkat.",
    "home.source": "Link atau lokasi berkas", "home.pick": "Pilih berkas", "home.count": "Jumlah klip",
    "home.countAuto": "Otomatis · 3–10 momen",
    "home.countHelp": "Otomatis menyesuaikan dengan durasi. Hasil bisa lebih sedikit jika sumber pendek.",
    "home.length": "Durasi klip", "home.lenAuto": "Otomatis · ikut momen",
    "home.len15": "Pendek · ±15 detik", "home.len30": "Sedang · ±30 detik", "home.len60": "Panjang · ±60 detik",
    "home.lengthHelp": "Batas dipotong di jeda kalimat terdekat agar tidak terpotong aneh.",
    "home.analysis": "Analisis momen",
    "home.analysisHelp": "Lokal gratis dan privat memakai model di perangkat. AI online memakai provider pilihanmu dan membutuhkan API key.",
    "home.localMode": "Analisis lokal", "home.localModeSub": "LLM terpasang / heuristik",
    "home.aiMode": "AI online", "home.aiModeSub": "Butuh API key",
    "home.aiProvider": "Provider AI", "home.aiProviderPick": "Pilih provider",
    "home.aiKey": "API key", "home.aiKeyPick": "API key milikmu", "home.aiKeySaved": "Tersimpan",
    "home.aiDetect": "Deteksi model", "home.aiModel": "Model AI", "home.aiModelAuto": "Otomatis · saran provider",
    "home.aiNeedProvider": "Pilih provider AI dulu.",
    "home.aiDetecting": "Memuat model dari provider…",
    "home.asrSpeed": "Model transkrip offline (Whisper)",
    "home.asrFast": "Cepat · model tiny", "home.asrBalanced": "Seimbang · model base", "home.asrAccurate": "Akurat · model small",
    "home.asrHelp": "Tiny memakai lebih sedikit RAM. Waktu dan ketepatan bergantung audio, bahasa, serta perangkat. Pilih model yang sudah terpasang.",
    "home.online": "Mode online",
    "home.onlineHelp": "Hybrid memeriksa caption dahulu; audio hanya jika diperlukan. Video segmen diambil saat preview atau render. Unduhan penuh hanya pada strategi online yang dipilih terpisah.",
    "home.linkMode": "Tautan video", "home.linkModeSub": "YouTube · TikTok · Instagram",
    "home.fileMode": "Berkas lokal", "home.fileModeSub": "MP4 dari perangkat",
    "home.onlineBadge": "video per segmen",
    "home.lang": "Bahasa konten",
    "home.transcript": "Subtitle AI dari audio (offline)", "home.transcriptHelp": "Studio ZAI mentranskrip audio video dengan model lokal, lalu membuat subtitle bertiming. Teks subtitle bawaan dari link tidak dipakai.", "home.llm": "Pilih momen dengan AI dari Pengaturan",
    "home.start": "Mulai buat klip", "home.doctor": "Cek perangkat", "home.recent": "Proyek terakhir",
    "home.quality": "Kualitas video", "home.advanced": "Pengaturan lanjutan",
    "home.linkReading": "Membaca link…", "home.linkReady": "Link siap", "home.linkFail": "Link tidak bisa dibaca",
    "home.localReady": "Berkas lokal siap",
    "projects.title": "Proyek", "projects.export": "Export gabungan", "projects.empty": "Belum ada proyek. Buat dari halaman Beranda.",
    "projects.deleteConfirm": "Hapus proyek ini beserta semua klipnya?",
    "clips.deleteConfirm": "Hapus klip ini? Berkas hasil rendernya ikut dihapus.",
    "clips.deleted": "Klip dihapus.",
    "editor.timeline": "Timeline", "editor.addText": "Tambah teks", "editor.addMedia": "Tambah media", "editor.addMusic": "Tambah musik",
    "editor.preparingPreview": "Menyiapkan pratinjau…",
    "editor.updatingPreview": "Memperbarui pratinjau…",
    "editor.previewFailed": "Pratinjau belum diperbarui",
    "editor.template": "Template teks", "editor.deleteItem": "Hapus item",
    "timeline.video": "Video", "timeline.media": "Media", "timeline.text": "Teks", "timeline.audio": "Audio",
    "voice.title": "Suara otomatis",
    "voice.lead": "Buat narasi dan kloning suara dari model lokal. Layanan online tetap opsional.",
    "voice.tts": "Text to speech", "voice.text": "Teks", "voice.lang": "Bahasa", "voice.model": "Model suara",
    "voice.generate": "Buat suara", "voice.clone": "Kloning suara",
    "voice.cloneNote": "Gunakan rekaman suaramu sendiri atau yang kamu punya izin. Pilih bahasa dan model sebelum membuat suara.",
    "voice.sample": "Contoh suara (6–30 detik, semua format yang dapat dibaca FFmpeg)", "voice.cloneRun": "Kloning", "voice.result": "Hasil",
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
    "settings.asrDevice": "ASR device",
    "hybrid.localOnly": "Full Offline requires a local file, not a link.",
    "project.relink": "Relink video", "project.sourcePath": "Original video's path after moving it",
    "project.relinkHint": "Choose the same video to keep trims, subtitles and exports consistent.",
    "hybrid.mode": "Processing mode", "hybrid.offline": "Full Offline · local file", "hybrid.online": "Online AI · optional",
    "hybrid.model": "Installed local LLM", "hybrid.none": "Not selected · heuristic fallback", "hybrid.detect": "Find local models",
    "hybrid.hint": "Captions first. Models are never downloaded automatically.", "hybrid.searching": "Finding installed models...",
    "hybrid.found": "{count} runtime models available.", "hybrid.gguf": "GGUF model on this computer", "hybrid.load": "Load GGUF model",
    "hybrid.stop": "Unload model from RAM", "hybrid.select": "Select model", "hybrid.stopped": "Model unloaded from RAM.",
    "nav.gallery": "Clip gallery", "gallery.lead": "All your project clips, ready to play, edit, and download again.",
    "gallery.empty": "No clips yet. Start with a long video on Home.", "gallery.draft": "Not rendered yet",
    "gallery.search": "Search clip or project title", "gallery.all": "All clips", "gallery.ready": "Rendered",
    "gallery.latest": "Latest", "gallery.score": "Highest score", "gallery.noMatch": "No matching clips.",
    "gallery.status": "Status", "gallery.order": "Sort by", "gallery.missing": "This clip was deleted. Refresh the gallery.",
    "clips.score": "Moment score", "clips.original": "Main", "clips.download": "Download", "clips.select": "Select for export",
    "batch.title": "Export multiple clips", "batch.help": "Choose clips and formats. Each output is saved separately and appears in the gallery.",
    "batch.all": "Select all", "batch.none": "Clear selection", "batch.render": "Render selection", "batch.required": "Select at least one clip and one format.",
    "batch.limit": "Select up to 20 clips per batch.", "batch.summary": "{clips} clips × {formats} formats = {total} videos",
    "batch.busy": "Wait for the active job to finish before starting another render.", "batch.done": "{total} videos created. Download them from the clip cards or Clip gallery.",
    "common.processing": "Processing",
    "editor.style": "Subtitle typography", "editor.trimHint": "Framing follows the selected canvas ratio.", "editor.timelineHint": "Select a block to edit. Drag its edge to trim. Video updates automatically.",
    "nav.home": "Home", "nav.projects": "Projects", "nav.voice": "Voice", "nav.models": "Models", "nav.settings": "Settings",
    "common.refresh": "Refresh", "common.back": "Back", "common.save": "Save", "common.cancel": "Cancel",
    "common.delete": "Delete", "common.render": "Render", "common.edit": "Edit", "common.close": "Close", "common.preview": "Preview",
    "home.title": "Choose a moment. Shape your clip.",
    "home.lead": "Paste a link or pick a video. 9:16 clips and subtitles are built locally on your device.",
    "home.source": "Link or file path", "home.pick": "Pick file", "home.count": "Number of clips",
    "home.countAuto": "Auto · 3–10 moments",
    "home.countHelp": "Auto adapts to duration. Results may be fewer for short sources.",
    "home.length": "Clip length", "home.lenAuto": "Auto · follow moments",
    "home.len15": "Short · ±15 sec", "home.len30": "Medium · ±30 sec", "home.len60": "Long · ±60 sec",
    "home.lengthHelp": "Bounds snap to the nearest sentence pause so cuts sound natural.",
    "home.analysis": "Moment analysis",
    "home.analysisHelp": "Local is free and private using on-device models. Online AI uses your chosen provider and needs an API key.",
    "home.localMode": "Local analysis", "home.localModeSub": "Installed LLM / heuristics",
    "home.aiMode": "Online AI", "home.aiModeSub": "Needs API key",
    "home.aiProvider": "AI provider", "home.aiProviderPick": "Pick a provider",
    "home.aiKey": "API key", "home.aiKeyPick": "Your API key", "home.aiKeySaved": "Saved",
    "home.aiDetect": "Detect models", "home.aiModel": "AI model", "home.aiModelAuto": "Auto · provider suggestion",
    "home.aiNeedProvider": "Pick an AI provider first.",
    "home.aiDetecting": "Loading models from provider…",
    "home.asrSpeed": "Offline transcription model (Whisper)",
    "home.asrFast": "Fast · tiny model", "home.asrBalanced": "Balanced · base model", "home.asrAccurate": "Accurate · small model",
    "home.asrHelp": "Tiny uses less RAM. Speed and accuracy depend on the audio, language and device. Choose an installed model.",
    "home.online": "Online mode",
    "home.onlineHelp": "Hybrid checks captions first and fetches audio only when needed. Video segments are fetched for preview or rendering. Full downloads use the separately selected online strategy.",
    "home.linkMode": "Link video", "home.linkModeSub": "YouTube · TikTok · Instagram",
    "home.fileMode": "Local file", "home.fileModeSub": "MP4 from your device",
    "home.onlineBadge": "selected segments",
    "home.lang": "Content language",
    "home.transcript": "AI subtitles from audio (offline)", "home.transcriptHelp": "Studio ZAI transcribes the video's audio with a local model and creates timed subtitles. Captions supplied by the link are not used.", "home.llm": "Use local LLM to pick moments",
    "home.start": "Start clipping", "home.doctor": "Check device", "home.recent": "Recent projects",
    "home.quality": "Video quality", "home.advanced": "Advanced settings",
    "home.linkReading": "Reading link…", "home.linkReady": "Link ready", "home.linkFail": "Could not read link",
    "home.localReady": "Local file ready",
    "projects.title": "Projects", "projects.export": "Export combined", "projects.empty": "No projects yet. Create one from Home.",
    "projects.deleteConfirm": "Delete this project and all its clips?",
    "clips.deleteConfirm": "Delete this clip? Its rendered file is removed too.",
    "clips.deleted": "Clip deleted.",
    "editor.timeline": "Timeline", "editor.addText": "Add text", "editor.addMedia": "Add media", "editor.addMusic": "Add music",
    "editor.preparingPreview": "Preparing preview…",
    "editor.updatingPreview": "Updating preview…",
    "editor.previewFailed": "Preview not updated",
    "editor.template": "Text template", "editor.deleteItem": "Delete item",
    "timeline.video": "Video", "timeline.media": "Media", "timeline.text": "Text", "timeline.audio": "Audio",
    "voice.title": "Voice",
    "voice.lead": "Generate and clone speech with local models. Online services remain optional.",
    "voice.tts": "Text to speech", "voice.text": "Text", "voice.lang": "Language", "voice.model": "Voice model",
    "voice.generate": "Generate voice", "voice.clone": "Voice cloning",
    "voice.cloneNote": "Use a recording of your own voice or one you have permission to use. Choose language and model first.",
    "voice.sample": "Voice sample (6–30 s, any FFmpeg-readable format)", "voice.cloneRun": "Clone", "voice.result": "Result",
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
  $$("[data-i18n-ph]").forEach((el) => {
    el.placeholder = t(el.dataset.i18nPh);
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
  updateBatchSummary();
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
  let completedExports = 0;
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
      if (job.kind === 'batch-render' && data.result?.exports?.length > completedExports) {
        completedExports = data.result.exports.length;
        if (state.project?.id === data.result.project) api(`/api/projects/${data.result.project}`).then(project => {
          state.project = project; renderProjects();
        }).catch(error => toast(error.message, 'error'));
      }
      const stageText = data.stage ? `${data.stage}: ${data.message || ""}` : (data.message || "");
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
      if (startBtn) { startBtn.disabled = false; syncAnalysisSourceUI(); }
      updateBatchSummary();
      if (data.status === "error") toast(data.error || t("toast.error"), "error");
      else if (data.status === "cancelled") toast(t("common.cancel"));
      else if (data.result?.zip) { const link=$('#batchZipDownload'); link.href=mediaUrl(data.result.zip);link.hidden=false;link.click();toast('ZIP klip siap'); }
      else if (data.result?.failures?.length) toast(`${data.result.exports?.length || 0} video selesai; ${data.result.failures.length} gagal: ${data.result.failures[0].error}`, "error");
      else if (data.result?.exports) toast(t("batch.done").replace("{total}", data.result.exports.length));
      else if (data.result?.failures && data.result.failures.length) {
        const first = data.result.failures[0];
        toast(`${t("toast.error")}: klip ${first.index + 1} · ${first.error}`, "error");
      }
      else toast(`${t("toast.done")}: ${data.title || ""}`);
      refreshAll();
      if (data.status === 'done' && data.result?.project?.execution?.task === 'transcript') openProject(data.result.project.id).catch(error => toast(error.message, 'error'));
      if (data.result?.image && window.renderImages) { setPage("images"); renderImages(); }
      if (data.result && data.result.path) playAudio(data.result.path);
    }
  };
  source.onerror = () => {
    source.close();
    const bar3 = $("#jobbar");
    if (bar3) bar3.classList.remove("visible");
    hideProcessing();
    if (startBtn) { startBtn.disabled = false; syncAnalysisSourceUI(); }
    state.jobId = null;
    updateBatchSummary();
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
  $$("#galleryGrid video").forEach((video) => video.pause());
  if (name !== 'voice') window.stopStudioRecording?.();
  $$(".page").forEach((page) => page.classList.toggle("active", page.id === `page-${name}`));
  $$("#nav button").forEach((button) => button.classList.toggle("active", button.dataset.page === name));
  if (name === "home") renderHomeProjects();
  if (name === "projects") renderProjects();
  if (name === "gallery") renderGallery();
  if (name === "models") renderModels();
  if (name === "settings") { renderSettings(); if (window.renderAiSettings) renderAiSettings(); }
  if (name === "images" && window.renderImages) renderImages();
  if (name === "voice") loadVoices().then(renderVoice).catch((error) => toast(error.message, "error"));
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
        .map((track) => `<option value="${escapeHtml(track.lang || track.format_id)}">${escapeHtml(track.label || track.lang)}</option>`)
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
      ${info.thumbnail ? `<img class="link-thumb" src="${escapeHtml(info.thumbnail)}" alt="" loading="lazy" />` : ""}
      <div style="display:grid;gap:2px;min-width:0">
        <span style="font-weight:600"><svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px;vertical-align:-2px"><path d="M20 6 9 17l-5-5"/></svg> ${t("home.linkReady")}</span>
        <span class="muted">${escapeHtml(info.title)} · ${fmtDuration(info.duration)}${info.uploader ? " · " + escapeHtml(info.uploader) : ""}</span>
      </div>
    </div>`;
}

function showLinkError(message) {
  const wrap = $("#linkPreviewWrap");
  const box = $("#linkPreview");
  wrap.style.display = "flex";
  $("#qualityWrap").style.display = "none";
  $("#audioTrackWrap").style.display = "none";
  linkInfoCache = null;
  box.innerHTML = `<span class="muted"><svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" style="width:14px;height:14px;vertical-align:-2px"><circle cx="12" cy="12" r="9"/><path d="M12 8v4M12 16h.01"/></svg> ${t("home.linkFail")}: ${message}</span>`;
}

function hideLinkPreview() {
  $("#linkPreviewWrap").style.display = "none";
  $("#qualityWrap").style.display = "none";
  $("#audioTrackWrap").style.display = "none";
  linkInfoCache = null;
}

function onSourceChanged() {
  const value = $("#source").value.trim();
  clearTimeout(linkInfoTimer);
  if (!value) { hideLinkPreview(); return; }
  const isUrl = /^https?:\/\//i.test(value);
  if (isUrl && $('#processingMode')?.value === 'offline') { hideLinkPreview(); return; }
  if (!isUrl) {
    // berkas lokal: tampilkan siap langsung
    const wrap = $("#linkPreviewWrap");
    const box = $("#linkPreview");
    wrap.style.display = "flex";
    $("#qualityWrap").style.display = "none";
    $("#audioTrackWrap").style.display = "none";
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
  if (state.jobId || homeSubmitting) return;
  const source = $("#source").value.trim();
  if (!source) {
    toast(t("home.source"), "error");
    return;
  }
  homeSubmitting = true;
  $('#startBtn').disabled = true;
  try {
    const task = document.querySelector('[name=creationTask]:checked').value;
    const useAiAnalysis = task === 'moments' && analysisSource() === 'ai';
    const processingMode = document.querySelector('#processingMode').value;
    if (processingMode === 'offline' && /^https?:\/\//i.test(source)) {
      toast(t('hybrid.localOnly'), 'error'); return;
    }
    if (useAiAnalysis) {
      const provider = $("#aiProvider").value;
      if (!provider) {
        toast(t("home.aiNeedProvider"), "error");
        return;
      }
      const aiValues = { ai_provider: provider };
      aiValues.ai_base_url = homeProviderBases[provider] || '';
      const typedKey = $("#aiKey").value.trim();
      if (typedKey) aiValues.ai_api_key = typedKey;
      const aiModel = $("#aiModel").value;
      aiValues.ai_model = aiModel || 'auto';
      await api("/api/settings", { method: "POST", body: JSON.stringify({ values: aiValues }) });
      homeAiKeySaved = homeAiKeySaved || Boolean(typedKey);
      refreshAiKeyBadge();
    }
    const project = await api("/api/projects", {
      method: "POST",
      body: JSON.stringify({ title: fileName(source) || "proyek", source: "", lang: $("#lang").value }),
    });
    const [minLen, maxLen] = CLIP_LENGTHS[$("#clipLength").value] || CLIP_LENGTHS.auto;
    const aiModelPick = useAiAnalysis ? $("#aiModel").value : 'auto';
    const job = await api(`/api/projects/${project.id}/process`, {
      method: "POST",
      body: JSON.stringify({
        source,
        task,
        processing_mode: useAiAnalysis ? 'online_ai' : processingMode,
        count: Number($("#count").value),
        analysis_mode: $("#analysisMode").value,
        review_first: $("#reviewFirst").checked,
        formats: [],
        min_len: minLen,
        max_len: maxLen,
        use_transcript: $("#useTranscript").checked,
        use_llm: task === 'moments' && (useAiAnalysis || Boolean(document.querySelector('#localModel').value)),
        model: useAiAnalysis ? (aiModelPick && aiModelPick !== 'auto' ? aiModelPick : null) : (document.querySelector('#localModel').value || null),
        asr_model: ASR_SPEED_MODELS[$("#asrSpeed").value] || null,
        quality: $("#quality").value || "720p",
        caption_motion: $("#homeCaptionMotion").value,
        subtitle_position: ($("#subPos") || {}).value || "bottom",
        canvas: ($("#canvasSize") || {}).value || "portrait",
        crop: $('#frameFit').value,
        audio_mode: ($("#audioMode") || {}).value || "original",
        audio_lang: (($("#audioTrack") || {}).value || "") || null,
        online: true,
      }),
    });
    trackJob(job);
  } catch (error) {
    toast(error.message, "error");
  } finally {
    homeSubmitting = false;
    if (!state.jobId) { $('#startBtn').disabled = false; syncAnalysisSourceUI(); }
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
    const clips = await api("/api/gallery");
    const box = $("#homeProjects");
    if (!clips.length) {
      box.innerHTML = `<div class="empty">Belum ada klip. Masukkan video untuk mencari momen pertama.</div>`;
      return;
    }
    box.innerHTML = clips.map(clip => `<article class="clip home-clip"><button class="clip-open clip-preview" data-home-edit="${escapeHtml(clip.project_id)}" data-storage="${escapeHtml(clip.storage_id)}" style="--preview-ratio:${previewAspect(clip.canvas,clip.source_width,clip.source_height)}" aria-label="Edit ${escapeHtml(clip.title)}">${clipThumbnailPath(clip.files) ? `<img class="thumb" loading="lazy" src="${mediaUrl(clipThumbnailPath(clip.files))}" alt="Frame klip">` : draftPoster(clip.project_id,clip)}${potentialBadge(clip.score)}<span class="clip-open-hint">${clip.edit_source ? 'Preview siap · Edit' : 'Buka editor'}</span></button><div class="meta"><span class="muted">${escapeHtml(clip.project_title)} · ${formatClock(clip.start)}–${formatClock(clip.end)}</span><strong>${escapeHtml(clip.title)}</strong><p class="clip-transcript">${escapeHtml(clip.transcript || 'Belum ada transkrip. Buat subtitle di editor.')}</p><button class="ghost" data-home-edit="${escapeHtml(clip.project_id)}" data-storage="${escapeHtml(clip.storage_id)}">Edit klip & transkrip</button></div></article>`).join('');
    box.querySelectorAll('[data-home-edit]').forEach(button => button.onclick = async () => {
      try { await openProject(button.dataset.homeEdit); const clip=state.project.clips.find(c=>c.storage_id===button.dataset.storage); if(clip)openEditor(clip.index); }
      catch(error){toast(error.message,'error');}
    });
    HomePreviewQueue.add(clips);
  } catch (error) {
    toast(error.message, "error");
  }
}

const HomePreviewQueue = (() => {
  const attempted=new Set(), pending=[]; let running=false,currentJob=null,paused=false;
  async function waitJob(id){
    for(;;){const job=await api(`/api/jobs/${id}`);if(job.status==='done')return job.result;
      if(['error','cancelled'].includes(job.status))throw new Error(job.error||'Persiapan dibatalkan');
      await new Promise(resolve=>setTimeout(resolve,1500));}
  }
  async function run(){
    if(running)return; running=true;
    while(pending.length&&!paused){
      const id=pending.shift(), status=$('#homePreviewStatus');
      status.textContent='Menyiapkan preview ringan di latar belakang · satu klip sekaligus.';
      try {
        const job=await api(`/api/projects/${encodeURIComponent(id)}/prepare-previews`,{method:'POST'});
        currentJob=job.id;$('#cancelHomePreviews').hidden=false;
        const result=await waitJob(job.id);
        status.textContent=result.failed?.length ? `${result.ready} preview siap; ${result.failed.length} belum tersedia. Buka editor untuk mencoba kembali.` : 'Preview siap. Perubahan teks dan gaya ditampilkan langsung di editor.';
        if(!document.querySelector('.editor-overlay:not([hidden])')) await renderHomeProjects();
      } catch(error){status.textContent=`Preview belum siap: ${error.message}`;}
    }
    running=false;currentJob=null;$('#cancelHomePreviews').hidden=true;
  }
  return {add(clips){for(const clip of clips){if(!clip.edit_source&&!attempted.has(clip.project_id)){attempted.add(clip.project_id);pending.push(clip.project_id);}}void run();},retry(){paused=false;attempted.clear();pending.length=0;void renderHomeProjects();},async stop(){paused=true;pending.length=0;if(currentJob)await api(`/api/jobs/${currentJob}/cancel`,{method:'POST'});$('#homePreviewStatus').textContent='Persiapan dihentikan. Preview yang sudah siap tetap tersimpan.';}};
})();
document.querySelector('#refreshHomeClips').onclick=()=>HomePreviewQueue.retry();
document.querySelector('#cancelHomePreviews').onclick=()=>HomePreviewQueue.stop().catch(error=>toast(error.message,'error'));

function previewAspect(canvas, width = 0, height = 0) {
  if (canvas === "portrait") return "9 / 16";
  if (canvas === "square") return "1 / 1";
  if (canvas === "classic") return "4 / 3";
  if (canvas === "original" && Number(width) > 0 && Number(height) > 0) return `${Math.min(8192, Number(width))} / ${Math.min(8192, Number(height))}`;
  return "16 / 9";
}

function potentialBadge(score) {
  if (score === null || score === undefined || !Number.isFinite(Number(score))) return "";
  const value = Math.round(Math.max(0, Math.min(1, Number(score))) * 100);
  const level = value >= 75 ? "high" : value >= 45 ? "medium" : "low";
  return `<span class="potential-score ${level}" title="Skor rekomendasi analisis. Semakin tinggi, semakin kuat potensi klip; tidak menjamin viral.">Skor ${value}<small>/100</small></span>`;
}

function renderedPreviewCanvas(files, canvas) {
  const path = clipPreviewPath(files || {});
  if (!path || files.mp4 === path) return canvas;
  for (const [key, value] of [["mp4_portrait", "portrait"], ["mp4_square", "square"], ["mp4_landscape", "landscape"]]) {
    if (files[key] === path) return value;
  }
  return canvas;
}

function projectCard(project) {
  const thumb = project.thumb ? `<img class="thumb" src="${mediaUrl(project.thumb)}" alt="" />` : project.source_thumbnail ? `<img class="thumb" src="${escapeHtml(project.source_thumbnail)}" alt="Gambar sumber video" loading="lazy" />` : `<div class="thumb">Preview belum tersedia</div>`;
  return `<article class="clip" data-project="${project.id}" style="cursor:pointer">
    <div class="clip-preview" style="--preview-ratio:${previewAspect(project.preview_canvas || 'portrait', project.width, project.height)}">${thumb}${potentialBadge(project.preview_score)}</div>
    <div class="meta">
      <strong>${escapeHtml(project.title)}</strong>
      <span class="score">${project.clips} klip · ${project.duration_label || formatClock(project.duration)} · ${project.language || ""}</span>
    </div>
  </article>`;
}

const exportFormats = [["mp4", ""], ["mp4_portrait", "9:16"], ["mp4_square", "1:1"], ["mp4_landscape", "16:9"]];
let galleryClips = [];
let galleryRequest = 0;
let batchProjectId = null;
let batchSelection = new Set();
let batchSubmitting = false;

function clipDownloadLinks(files = {}) {
  return exportFormats.filter(([key]) => files[key]).map(([key, label]) =>
    `<a class="download-link" href="${mediaUrl(files[key])}" download>${t("clips.download")} ${label || t("clips.original")}</a>`
  ).join("");
}

function clipPreviewPath(files = {}) {
  return exportFormats.map(([key]) => files[key]).find(Boolean);
}

function draftPoster(projectId, clip) {
  const url = `/api/projects/${encodeURIComponent(projectId)}/clips/${clip.index}/poster?storage=${encodeURIComponent(clip.storage_id)}&start=${encodeURIComponent(clip.start)}`;
  return `<img class="thumb clip-frame" src="${escapeHtml(url)}" alt="Frame awal klip" loading="lazy" />`;
}
document.addEventListener('error', event => {
  if (!event.target.matches?.('img.clip-frame')) return;
  const notice = document.createElement('div');
  notice.className = 'gallery-draft';
  notice.textContent = 'Frame klip belum tersedia. Buka sumber atau muat ulang untuk mencoba lagi.';
  event.target.replaceWith(notice);
}, true);

function clipThumbnailPath(files = {}) {
  const key = exportFormats.find(([name]) => files[name])?.[0] || "mp4";
  return files[key.replace("mp4", "thumb")] || files.thumb;
}

async function renderGallery() {
  const request = ++galleryRequest;
  try {
    const clips = await api("/api/gallery");
    if (request !== galleryRequest) return;
    galleryClips = clips;
    paintGallery();
  } catch (error) {
    if (request === galleryRequest) $("#galleryGrid").innerHTML = `<div class="empty">${escapeHtml(error.message)}</div>`;
  }
}

function paintGallery() {
  const grid = $("#galleryGrid");
  grid.querySelectorAll("video").forEach((video) => video.pause());
  const query = $("#gallerySearch").value.trim().toLocaleLowerCase();
  const readyOnly = $("#galleryStatus").value === "ready";
  const clips = galleryClips.filter((clip) =>
    (!readyOnly || clipPreviewPath(clip.files)) && `${clip.title} ${clip.project_title}`.toLocaleLowerCase().includes(query)
  );
  clips.sort($("#gallerySort").value === "score"
    ? (a, b) => Number(b.score || 0) - Number(a.score || 0)
    : (a, b) => b.updated - a.updated || a.index - b.index);
  grid.innerHTML = clips.length ? clips.map((clip) => {
    const files = clip.files || {};
    const preview = clipPreviewPath(files);
    const poster = clipThumbnailPath(files);
    const media = preview
      ? `<video controls playsinline preload="none" ${poster ? `poster="${mediaUrl(poster)}"` : ""} src="${mediaUrl(preview)}" aria-label="${escapeHtml(clip.title)}"></video>`
      : draftPoster(clip.project_id, clip);
    return `<article class="clip gallery-clip"><div class="clip-preview" style="--preview-ratio:${previewAspect(renderedPreviewCanvas(files, clip.canvas), clip.source_width, clip.source_height)}">${media}${potentialBadge(clip.score)}</div>
      <div class="meta"><span class="score">${escapeHtml(clip.project_title)}</span><strong>${escapeHtml(clip.title)}</strong>
      <span class="score">${formatClock(clip.start)}–${formatClock(clip.end)} · ${t("clips.score")} ${Number(clip.score || 0).toFixed(2)}</span></div>
      <div class="gallery-actions"><button class="mini" data-gallery-open="${escapeHtml(clip.project_id)}" data-storage="${escapeHtml(clip.storage_id)}">${t("common.edit")}</button>${clipDownloadLinks(files)}</div></article>`;
  }).join("") : `<div class="empty">${t(galleryClips.length ? "gallery.noMatch" : "gallery.empty")}</div>`;
  grid.querySelectorAll("[data-gallery-open]").forEach((button) => button.addEventListener("click", async () => {
    try {
      await openProject(button.dataset.galleryOpen);
      const clip = state.project.clips.find((item) => item.storage_id === button.dataset.storage);
      if (!clip) return toast(t("gallery.missing"), "error");
      openEditor(clip.index);
    }
    catch (error) { toast(error.message, "error"); }
  }));
  grid.querySelectorAll("video").forEach((video) => video.addEventListener("play", () => {
    grid.querySelectorAll("video").forEach((other) => { if (other !== video) other.pause(); });
  }));
}

function updateBatchSummary() {
  const clips = $$("#clipGrid [data-batch-clip]:checked").length;
  const formats = $$("#batchPanel .batch-formats input:checked").length;
  $("#batchSummary").textContent = t("batch.summary").replace("{clips}", clips).replace("{formats}", formats).replace("{total}", clips * formats);
  $("#batchZipBtn").disabled = !clips || !formats || Boolean(state.jobId) || batchSubmitting;
  $("#batchRenderBtn").disabled = !clips || !formats || clips > 20 || Boolean(state.jobId) || batchSubmitting;
}

async function renderSelectedClips() {
  if (!state.project) return;
  if (state.jobId || batchSubmitting) return toast(t("batch.busy"));
  const clips = $$("#clipGrid [data-batch-clip]:checked").map((input) => Number(input.dataset.batchClip));
  const formats = $$("#batchPanel .batch-formats input:checked").map((input) => input.value);
  if (!clips.length || !formats.length) return toast(t("batch.required"), "error");
  if (clips.length > 20) return toast(t("batch.limit"), "error");
  batchSubmitting = true;
  updateBatchSummary();
  try {
    const job = await api(`/api/projects/${state.project.id}/batch-render`, {
      method: "POST", body: JSON.stringify({ clips, formats }),
    });
    trackJob(job);
  } catch (error) { toast(error.message, "error"); }
  finally { batchSubmitting = false; updateBatchSummary(); }
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
          <span style="font-weight:600">${escapeHtml(project.title)}</span>
          <span class="muted">${project.clips} klip · ${project.duration_label || ""} · ${new Date(project.updated * 1000).toLocaleDateString()}</span>
        </div>
        <div class="row" style="gap:var(--s2)">
          <button class="mini" data-open="${project.id}">${t("common.edit")}</button>
          <button class="mini danger" data-delete="${project.id}">${t("common.delete")}</button>
        </div>
      </div>`).join("")}</div>`;
    list.querySelectorAll("[data-open]").forEach((node) => node.addEventListener("click", () => openProject(node.dataset.open)));
    list.querySelectorAll("[data-delete]").forEach((node) =>
      node.addEventListener("click", async () => {
        if (!await confirmAction(t("projects.deleteConfirm"))) return;
        try {
          await api(`/api/projects/${node.dataset.delete}`, { method: "DELETE" });
          await Promise.all([renderProjects(), renderHomeProjects()]);
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
  if (batchProjectId !== project.id) {
    batchProjectId = project.id;
    batchSelection = new Set(project.clips.slice(0, 20).map((clip) => clip.storage_id));
  }
  $("#batchPanel").hidden = !project.clips.length;
  $("#projectList").innerHTML = "";
  $("#projectDetail").style.display = "block";
  $("#detailTitle").textContent = project.title;
  $("#detailMeta").textContent = `${project.clips.length} klip · ${formatClock(project.duration)} · ${project.language || ""}`;
  let execution = document.querySelector('#executionPath');
  if (!execution) { execution = document.createElement('p'); execution.id = 'executionPath'; execution.className = 'field-help'; $('#detailMeta').after(execution); }
  execution.textContent = [project.execution?.transcript, project.execution?.ranking, project.notes].filter(Boolean).join(' · ');
  let transcriptPanel = $('#projectTranscript');
  if (!transcriptPanel) {
    transcriptPanel = document.createElement('details'); transcriptPanel.id = 'projectTranscript'; transcriptPanel.className = 'card transcript-panel';
    $('#clipGrid').before(transcriptPanel);
  }
  const segments = project.transcript?.segments || [];
  transcriptPanel.hidden = !segments.length;
  transcriptPanel.open = project.execution?.task === 'transcript';
  transcriptPanel.innerHTML = `<summary>Transkrip · ${segments.length} bagian</summary><a class="button" href="/api/projects/${encodeURIComponent(project.id)}/transcript.srt" download>Unduh SRT</a><div class="transcript-rows">${segments.map(s => `<p><time>${formatClock(s.start)}</time> ${escapeHtml(s.text || '')}</p>`).join('')}</div>`;
  let relink = document.querySelector('#relinkSource');
  if(!relink){
    relink=document.createElement('details'); relink.id='relinkSource'; relink.className='field';
    relink.innerHTML=`<summary>${t('project.relink')}</summary><label for="relinkPath">${t('project.sourcePath')}</label><input id="relinkPath" type="text"><p class="field-help">${t('project.relinkHint')}</p><div class="actions"><button type="button" id="pickRelink">${t('home.pick')}</button><button type="button" id="applyRelink">${t('project.relink')}</button></div><p id="relinkStatus" role="status"></p>`;
    $('#detailMeta').after(relink);
    $('#pickRelink').hidden=!window.pywebview?.api;
    $('#pickRelink').onclick=async()=>{const path=await window.pywebview.api.pick_file();if(path)$('#relinkPath').value=path;};
    $('#applyRelink').onclick=async()=>{
      if(state.jobId){$('#relinkStatus').textContent=t('batch.busy');return;}
      try{state.project=await api(`/api/projects/${state.project.id}/relink`,{method:'POST',body:JSON.stringify({source:$('#relinkPath').value.trim()})});renderProjectDetail();}
      catch(error){$('#relinkStatus').textContent=error.message;}
    };
  }
  relink.hidden=project.online;
  let sourceAction = $("#sourceAction");
  if (!sourceAction) {
    sourceAction = document.createElement("button"); sourceAction.id = "sourceAction";
    sourceAction.className = "ghost"; sourceAction.textContent = "＋ Ambil bagian dari video sumber";
    $("#detailMeta").after(sourceAction);
    sourceAction.addEventListener("click", openSourceEditor);
  }
  sourceAction.disabled = !project.source || !project.duration;
  const grid = $("#clipGrid");
  let scoreHelp = $("#clipScoreHelp");
  if (!scoreHelp) {
    scoreHelp = document.createElement("p");
    scoreHelp.id = "clipScoreHelp";
    scoreHelp.className = "muted";
    grid.before(scoreHelp);
  }
  scoreHelp.textContent = "Skor lebih tinggi menunjukkan rekomendasi potensi yang lebih kuat. Skor ini tidak menjamin viral.";
  if (!project.clips.length) {
    grid.innerHTML = `<div class="empty">${segments.length ? 'Transkrip siap. Belum ada klip yang dibuat dari proyek ini.' : 'Belum ada klip. Proses sumber dari Beranda atau pilih bagian video secara manual.'}</div>`;
    return;
  }
  grid.innerHTML = project.clips.map((clip) => {
    const poster = clipThumbnailPath(clip.files);
    const thumb = poster
      ? `<img class="thumb" src="${mediaUrl(poster)}" alt="" loading="lazy" />`
      : draftPoster(project.id, clip);
    const ready = Boolean(clipPreviewPath(clip.files));
    const status = (ready ? `<span class="badge ok">siap</span>` : `<span class="badge warn">draft</span>`) + (project.execution?.ranking === "heuristic-only" ? `<span class="badge">heuristik</span>` : "");
    return `<article class="clip">
      <button type="button" class="clip-open clip-preview" style="--preview-ratio:${previewAspect(renderedPreviewCanvas(clip.files || {}, clip.canvas), project.width, project.height)}" data-edit="${clip.index}" aria-label="Buka ${escapeHtml(clip.title || 'klip')} di editor">${thumb}${potentialBadge(clip.score)}<span class="clip-open-hint">Putar &amp; edit</span></button>
      <div class="meta">
        <label class="clip-select"><input type="checkbox" data-batch-clip="${clip.index}" data-storage="${clip.storage_id}" ${batchSelection.has(clip.storage_id) ? "checked" : ""} />${t("clips.select")}</label>
        <strong>${escapeHtml(clip.title || "Klip " + (clip.index + 1))}</strong>
        <span class="score">${formatClock(clip.start)}–${formatClock(clip.end)} · skor ${(clip.score || 0).toFixed(2)}</span>
        <span>${status} <span class="badge">${clip.crop}</span></span>
        <div class="gallery-actions">${clipDownloadLinks(clip.files)}</div>
      </div>
      <div class="actions">
        <button class="icon-btn" data-edit="${clip.index}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/></svg>${t("common.edit")}</button>
        <button class="icon-btn" data-render="${clip.index}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-3-6.7M21 3v6h-6"/></svg>${t("common.render")}</button>
        <button class="icon-btn" data-remove="${clip.index}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 6h18M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2m2 0v14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V6"/></svg>${t("common.delete")}</button>
      </div>
    </article>`;
  }).join("");

  updateBatchSummary();
  grid.querySelectorAll("[data-batch-clip]").forEach((input) => input.addEventListener("change", () => {
    if (input.checked) batchSelection.add(input.dataset.storage);
    else batchSelection.delete(input.dataset.storage);
    updateBatchSummary();
  }));
  grid.querySelectorAll("[data-edit]").forEach((node) => node.addEventListener("click", () => openEditor(Number(node.dataset.edit))));
  grid.querySelectorAll("[data-render]").forEach((node) =>
    node.addEventListener("click", async () => {
      const job = await api(`/api/projects/${project.id}/clips/${node.dataset.render}/render`, { method: "POST" });
      trackJob(job);
    })
  );
  grid.querySelectorAll("[data-remove]").forEach((node) =>
    node.addEventListener("click", async () => {
      if (!await confirmAction(t("clips.deleteConfirm"))) return;
      try {
        await api(`/api/projects/${project.id}/clips/${node.dataset.remove}`, { method: "DELETE" });
        state.project = await api(`/api/projects/${project.id}`);
        renderProjectDetail();
        await renderHomeProjects();
        toast(t("clips.deleted"), "ok");
      } catch (error) {
        toast(error.message, "error");
      }
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
  const panel = $("#editPanel");
  panel.querySelectorAll("video,audio").forEach((player) => {
    player.pause();
    player.removeAttribute("src");
    player.load();
  });
  panel.classList.remove("open");
  panel.replaceChildren();
}

/* ------------------------------------------------------------------ voice */

function voiceLabel(id) {
  if (id === "supertonic-3-int8") return "Supertonic 3 · 10 suara";
  const fake = { id, size_mb: null, note: "", langs: [] };
  if (id.includes("id_ID")) fake.langs = ["id"];
  else if (id.includes("en_")) fake.langs = ["en"];
  return modelName(fake).replace(/ — \? MB$/, "");
}

function voiceModel(id) {
  const rootId = id.split(":")[0];
  return (state.voices.models || []).find(model => model.id === rootId) || null;
}

function voiceRights(model) {
  if (!model) return "Lisensi belum diketahui";
  const status = model.commercial_use;
  const label = status === "allowed" && model.license_kind === "open-weights" ? "komersial dengan syarat lisensi"
    : status === "allowed" ? "komersial diizinkan" : status === "conditional" ? "komersial bersyarat" : status === "restricted" ? "nonkomersial" : "hak komersial belum terverifikasi";
  return `${model.license || "Lisensi belum tercatat"} · ${label}`;
}

function renderVoice() {
  const select = $("#ttsVoice");
  const previousVoice = select.value;
  const language = $("#ttsLang").value;
  const installed = state.voices.piper || [];
  const available = installed.filter(id => (voiceModel(id)?.langs || []).includes(language) && id !== "supertonic-3-int8");
  if (installed.includes("supertonic-3-int8")) {
    available.unshift(...Array.from({ length: 10 }, (_, sid) => `supertonic-3-int8:${sid}`));
  }
  select.innerHTML = available.map((id) => {
    const model = voiceModel(id);
    const rights = model?.commercial_use === "restricted" ? " · nonkomersial"
      : model?.commercial_use === "unverified" ? " · hak belum jelas" : "";
    return `<option value="${escapeHtml(id)}">${id.startsWith("supertonic-3-int8:") ? `Supertonic 3 · Suara ${Number(id.split(":")[1]) + 1}` : voiceLabel(id)}${rights}</option>`;
  }).join("");
  select.disabled = available.length === 0;
  if (available.includes(previousVoice)) select.value = previousVoice;
  const ttsBtn = $("#ttsBtn");
  if (ttsBtn) {
    ttsBtn.disabled = available.length === 0 && $("#ttsEngine")?.value !== "cloud";
    ttsBtn.title = available.length === 0 ? "Unduh dulu model suara di halaman Model" : "";
  }
  if (available.length === 0) {
    select.innerHTML = `<option value="">— belum ada model suara —</option>`;
  }
  const selectedVoice = voiceModel(select.value);
  $("#ttsModelHint").textContent = selectedVoice
    ? `${voiceRights(selectedVoice)}. ${selectedVoice.license_note || selectedVoice.note || ""}`
    : "Pasang model suara di halaman Model untuk memakai TTS offline.";

  const cloneLang = $("#cloneLang").value;
  const cloneSelect = $("#cloneModel");
  const installedClone = (state.voices.clone || []).filter(id => (voiceModel(id)?.langs || []).includes(cloneLang));
  const previousClone = cloneSelect.value;
  cloneSelect.innerHTML = installedClone.length
    ? installedClone.map(id => `<option value="${escapeHtml(id)}">${escapeHtml(voiceLabel(id))}</option>`).join("")
    : `<option value="">— belum ada model untuk bahasa ini —</option>`;
  if (installedClone.includes(previousClone)) cloneSelect.value = previousClone;
  cloneSelect.disabled = !installedClone.length;
  $("#cloneBtn").disabled = !installedClone.length;
  const selectedClone = voiceModel(cloneSelect.value);
  const uninstalled = (state.voices.models || []).find(model => model.kind === "clone" && (model.langs || []).includes(cloneLang));
  $("#cloneModelHint").textContent = selectedClone
    ? `${voiceRights(selectedClone)}. ${selectedClone.runtime_note || selectedClone.note || ""}`
    : uninstalled ? `${uninstalled.installed ? "Bobot sudah ada, runtime belum siap" : "Belum terpasang"}: ${voiceLabel(uninstalled.id)} (${uninstalled.size_mb || "?"} MB). ${uninstalled.runtime_note || uninstalled.note || ""}`
      : "Belum ada model kloning lokal untuk bahasa ini.";
  $("#cloneReferenceWrap").hidden = cloneSelect.value !== "zipvoice-zh-en";
  $("#cloneHint").textContent = !state.settings.clone_consent ? t("settings.consent") : "";
}

async function runTts() {
  const text = $("#ttsText").value.trim();
  if (!text) return toast(t("voice.text"), "error");
  try {
    if ($('#ttsEngine')?.value === 'cloud') {
      const job = await api('/api/ai/speech', { method: 'POST', body: JSON.stringify({ text, voice: $('#cloudVoice').value, language: $('#ttsLang').value }) });
      trackJob(job);
      return;
    }
    const job = await api("/api/tts", {
      method: "POST",
      body: JSON.stringify({ text, lang: $("#ttsLang").value, voice_id: $("#ttsVoice").value || null }),
    });
    trackJob(job);
  } catch (error) {
    toast(error.message, "error");
  }
}

async function runClone() {
  const text = $("#cloneText").value.trim();
  const sample = $("#cloneSample").value.trim();
  const modelId = $("#cloneModel").value;
  if (!text) return toast("Isi teks yang akan diucapkan.", "error");
  if (!sample) return toast("Pilih atau rekam contoh suara dulu.", "error");
  if (!modelId) return toast("Pasang model kloning untuk bahasa pilihanmu.", "error");
  if (modelId === "zipvoice-zh-en" && !$("#referenceText").value.trim()) {
    return toast("Isi ucapan persis pada rekaman contoh untuk ZipVoice.", "error");
  }
  state.settings.clone_sample = sample;
  try {
    const job = await api("/api/clone", {
      method: "POST",
      body: JSON.stringify({ text, sample, lang: $("#cloneLang").value, model_id: modelId, reference_text: $("#referenceText").value }),
    });
    trackJob(job);
  } catch (error) { toast(error.message, "error"); }
}

async function uploadCloneSample(file) {
  if (!file) return;
  const button = $("#pickSample");
  button.disabled = true;
  button.textContent = "Menyiapkan audio…";
  try {
    const response = await fetch("/api/voice-sample", { method: "POST", body: file });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Berkas tidak dapat dibaca");
    $("#cloneSample").value = payload.path;
    $("#cloneSampleName").textContent = file.name;
    const player = $("#cloneSamplePlayer");
    player.src = mediaUrl(payload.path);
    player.hidden = false;
    toast("Contoh suara siap dipakai.");
  } catch (error) { toast(error.message, "error"); }
  finally { button.disabled = false; button.textContent = t("home.pick"); }
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
    const voices = {news_tts: "News", lessac: "Lessac", alba: "Alba", amy: "Amy", ryan: "Ryan", joe: "Joe", ljspeech: "LJ"};
    const voice = Object.entries(voices).find(([key]) => id.includes(key))?.[1] || "";
    return `Suara ${lang}${voice ? ` ${voice}` : ""} — ${model.size_mb ?? "?"} MB`;
  }
  if (id === "supertonic-3-int8") return `Supertonic 3 · 10 suara ID/EN — ${model.size_mb ?? "?"} MB`;
  if (id === "chatterbox-base") return `Kloning Suara EN — ${model.size_mb ?? "?"} MB`;
  if (id === "chatterbox-id-finetune") return `Kloning Suara Indonesia — ${model.size_mb ?? "?"} MB`;
  if (id === "zipvoice-zh-en") return `Kloning Ringan EN — ${model.size_mb ?? "?"} MB`;
  if (id === "chatterbox-gguf-q4") return `Kloning Eksperimental — ${model.size_mb ?? "?"} MB`;
  if (id === "mms-tts-ind") return `Suara Indonesia Alternatif — ${model.size_mb ?? "?"} MB`;
  return `${id}${size}`;
}

function kindName(kind) {
  return kind === "asr" ? t("models.kindAsr")
    : kind === "tts" ? t("models.kindTts")
    : kind === "image" ? "Gambar"
    : t("models.kindClone");
}

function modelRightsBadge(model) {
  const usage = model.commercial_use;
  const label = usage === "allowed" && model.license_kind === "open-weights" ? "Komersial bersyarat"
    : usage === "allowed" ? "Komersial ✓"
    : usage === "conditional" ? "Komersial bersyarat"
      : usage === "restricted" ? "Nonkomersial" : "Hak komersial belum jelas";
  const tone = usage === "allowed" ? "ok" : usage === "restricted" ? "error" : "";
  return `<span class="badge ${tone}" title="${escapeHtml(model.license_note || "")}">${label}</span>`;
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
            <span class="muted">${kindName(model.kind)}${model.note ? " · " + escapeHtml(model.note) : ""}</span>
            <span class="muted">${escapeHtml(model.license || "Lisensi belum tercatat")}${model.license_note ? " · " + escapeHtml(model.license_note) : ""}${model.license_url ? ` · <a href="${escapeHtml(model.license_url)}" target="_blank" rel="noopener noreferrer">Lihat syarat</a>` : ""}</span>
            ${model.runtime_note ? `<span class="muted">${escapeHtml(model.runtime_note)}</span>` : ""}
          </div>
          <div class="row" style="gap:var(--s2)">
            ${modelRightsBadge(model)}
            ${model.installed ? `<span class="badge ok">${t("models.installed")}</span>` : (model.requires_pip ? `<span class="badge">${t("models.pip")}</span>` : "")}
            ${model.installed ? `<button class="mini danger" data-remove-model="${model.id}">${t("models.remove")}</button>`
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
  $("#setAsrDevice").value = settings.asr_device || 'auto';
  const asrIds = ["whisper-tiny-int8", "whisper-base-int8", "whisper-small-int8", "whisper-medium-int8"];
  $("#setAsr").innerHTML = asrIds
    .map((id) => `<option value="${id}" ${settings.asr_model === id ? "selected" : ""}>${voiceLabel(id)}</option>`).join("");
  const ttsIds = state.voices.piper.filter((id) => id.includes("id_ID") || id === "supertonic-3-int8");
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
    asr_device: $("#setAsrDevice").value,
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
      `;
    $("#wzStart").addEventListener("click", () => wizardDetect());

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
    const recommended = [tier.asr, tier.tts, "piper-en_US-ljspeech-medium"].filter(Boolean);
    wizard.chosen = recommended.slice();
    wizardShowRecommend();
  } catch (error) {
    body.textContent = `Gagal mendeteksi: ${error.message}`;
    actions.innerHTML = `<button class="primary" id="wzRetry">Coba lagi</button>`;
    $("#wzRetry").addEventListener("click", wizardDetect);
  }
}

function wizardShowRecommend() {
  const device = wizard.device;
  const tier = wizard.data.tier;
  $("#wizardTitle").textContent = "Perangkatmu terdeteksi";
  $("#wizardSub").textContent = `${device.os} · RAM ${device.ram_gb ?? "?"} GB · ${device.cpu_count} core · disk bebas ${device.disk_free_gb} GB`;

  const rows = wizard.models.filter((model) => !model.requires_pip || model.kind === "asr").map((model) => {
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
    <p class="muted">FFmpeg, transkripsi, Piper, dan runtime ZipVoice termasuk paket Windows. Unduh model sesuai fitur yang dibutuhkan. Model gambar lokal SDXS-512 dapat dipasang kapan saja dari Studio gambar.</p>
    ${rows}`;
  $("#wizardActions").innerHTML = `
    <button class="primary" id="wzInstall">Unduh & pasang</button>
    `;

  $("#wizardBody").querySelectorAll("[data-model]").forEach((cb) =>
    cb.addEventListener("change", () => {
      const id = cb.dataset.model;
      if (cb.checked && !wizard.chosen.includes(id)) wizard.chosen.push(id);
      if (!cb.checked) wizard.chosen = wizard.chosen.filter((x) => x !== id);
    })
  );
  $("#wzInstall").addEventListener("click", wizardInstall);

}

async function wizardInstall() {
  if (wizard.busy) return;
  wizard.busy = true;
  wizard.chosen = [...new Set([...wizard.chosen, wizard.data.tier.asr, wizard.data.tier.tts])];
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
  await wizardFinish();
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
  const current = await api("/api/models");
  const required = [wizard.data.tier.asr, wizard.data.tier.tts];
  const missing = [...new Set([...required, ...wizard.chosen])].filter((id) => !current.models.some((m) => m.id === id && m.installed));
  if (missing.length) {
    $("#wizardTitle").textContent = "Setup belum selesai";
    $("#wizardSub").textContent = `Model belum terpasang: ${missing.join(", ")}. Coba lagi untuk melanjutkan unduhan.`;
    $("#wizardActions").innerHTML = '<button class="primary" id="wzRetry">Coba lagi</button>';
    $("#wzRetry").addEventListener("click", wizardDetect);
    return;
  }
  await api("/api/settings", {method: "POST", body: JSON.stringify({values: {asr_model: required[0], tts_voice_id: required[1]}})});
  $("#wizardTitle").textContent = "Siap dipakai";
  $("#wizardSub").textContent = "Model terpasang. Semua fitur inti jalan lokal dan offline.";
  $("#wizardBody").innerHTML = "";
  $("#wizardActions").innerHTML = `<button class="primary" id="wzGo">Mulai pakai</button>`;
  $("#wzGo").addEventListener("click", wizardDone);
  await refreshAll();
}

async function wizardDone() {
  await api("/api/settings", { method: "POST", body: JSON.stringify({ values: { setup_done: true, setup_version: 2 } }) });
  $("#wizardOverlay").hidden = true;
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
    if (settings.setup_version !== 2) {
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
  if ($("#page-gallery").classList.contains("active")) renderGallery();
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
    if (input.files[0]) CreatorEditor.upload(input.files[0], target).catch(error => toast(error.message, "error"));
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
  await initHomeAnalysis();
  $("#homeMotionPicker").innerHTML = CaptionMotion.picker("homeCaptionMotion");
  CaptionMotion.demo($("#homeMotionDemo"), $("#homeCaptionMotion"));
  HomeGuide.init();

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
    refreshAiKeyBadge();
    refreshAll();
  });
  $("#startBtn").addEventListener("click", startClipping);
  $("#doctorBtn").addEventListener("click", showDoctor);
  // Wizard bisa dibuka kapan saja dari halaman Model (tidak hanya saat pertama kali).
  const wizardBtn = $("#openWizard");
  if (wizardBtn) wizardBtn.addEventListener("click", () => wizardShow(0));
  $("#source").addEventListener("input", onSourceChanged);
  $("#pickFile").addEventListener("click", () => pickFile("#source"));
  $("#pickSample").addEventListener("click", () => $("#cloneFileInput").click());
  $("#cloneFileInput").addEventListener("change", (event) => uploadCloneSample(event.target.files?.[0]));
  $("#cloneLang").addEventListener("change", renderVoice);
  $("#cloneModel").addEventListener("change", renderVoice);
  $("#ttsVoice").addEventListener("change", renderVoice);
  $("#refreshProjects").addEventListener("click", () => { state.project = null; renderProjects(); });
  $("#refreshGallery").addEventListener("click", renderGallery);
  $("#gallerySearch").addEventListener("input", paintGallery);
  $("#galleryStatus").addEventListener("change", paintGallery);
  $("#gallerySort").addEventListener("change", paintGallery);
  $("#batchPanel").addEventListener("change", updateBatchSummary);
  $("#selectAllClips").addEventListener("click", () => {
    $$("#clipGrid [data-batch-clip]").forEach((input, position) => {
      input.checked = position < 20;
      if (input.checked) batchSelection.add(input.dataset.storage);
      else batchSelection.delete(input.dataset.storage);
    });
    if ((state.project?.clips.length || 0) > 20) toast(t("batch.limit"));
    updateBatchSummary();
  });
  $("#clearClipSelection").addEventListener("click", () => {
    batchSelection.clear();
    $$("#clipGrid [data-batch-clip]").forEach((input) => { input.checked = false; });
    updateBatchSummary();
  });
  $("#batchRenderBtn").addEventListener("click", renderSelectedClips);
  $("#batchZipBtn").onclick=async()=>{ if(!state.project||state.jobId)return;try { const clips=$$("#clipGrid [data-batch-clip]:checked").map(i=>Number(i.dataset.batchClip)), formats=$$("#batchPanel .batch-formats input:checked").map(i=>i.value); const job=await api(`/api/projects/${state.project.id}/clips-zip`,{method:'POST',body:JSON.stringify({clips,formats})});$('#batchZipDownload').hidden=true;trackJob(job); } catch(e){toast(e.message,'error');} };
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

// Explicit source modes keep the path visible and explain the next action.
document.querySelectorAll('[data-source-mode]').forEach(button => button.addEventListener('click', () => {
  document.querySelectorAll('[data-source-mode]').forEach(node => {
    const on = node === button;
    node.classList.toggle('active', on);
    node.setAttribute('aria-selected', on ? 'true' : 'false');
  });
  const local = button.dataset.sourceMode === 'file';
  document.querySelector('#source').placeholder = local ? 'D:\\Video\\podcast.mp4' : 'https://youtube.com/watch?v=…';
  document.querySelector('#sourceHelp').textContent = local ? 'Pilih video dari perangkat, atau tempel lokasi lengkap berkas. Video lokal tidak perlu diunduh.' : 'Tempel tautan YouTube, TikTok, atau Instagram. Kualitas dan track audio muncul setelah tautan terbaca.';
  document.querySelector('#pickFile').hidden = !local;
  document.querySelector('#source').focus();
}));

// Home analysis controls: local vs AI online, provider/key/model, ASR speed.
const ASR_SPEED_MODELS = { fast: 'whisper-tiny-int8', balanced: 'whisper-base-int8', accurate: 'whisper-small-int8' };
const CLIP_LENGTHS = { auto: [0, 0], s15: [10, 20], s30: [20, 40], s60: [45, 75] };
let homeAiKeySaved = false;
let homeSubmitting = false;
let homeDiscoveryGeneration = 0;
let homeProviderBases = {};

function analysisSource() {
  return document.querySelector('[data-analysis-source].active')?.dataset.analysisSource || 'local';
}

function refreshAiKeyBadge() {
  const badge = document.querySelector('#aiKeyState');
  if (!badge) return;
  badge.hidden = !homeAiKeySaved;
  if (homeAiKeySaved) badge.textContent = t('home.aiKeySaved');
}

function syncAnalysisSourceUI() {
  const transcriptOnly = document.querySelector('[name=creationTask]:checked')?.value === 'transcript';
  const ai = !transcriptOnly && analysisSource() === 'ai';
  const mode = document.querySelector('#processingMode');
  if (mode && transcriptOnly) mode.value = 'local';
  if (mode && ai) mode.value = 'online_ai';
  else if (mode && mode.value === 'online_ai') mode.value = 'local';
  document.querySelector('#aiPanel').hidden = !ai;
  document.querySelector('#localLlmFields').hidden = ai || transcriptOnly;
  document.querySelector('#momentModelControls').hidden = transcriptOnly;
  document.querySelector('.analysis-modes').hidden = true;
  document.querySelector('#clipResultSettings').hidden = transcriptOnly;
  document.querySelector('#advDetails').hidden = transcriptOnly;
  document.querySelector('[aria-labelledby=analysisHeading]').hidden = transcriptOnly;
  document.querySelector('#analysisHeading').textContent = transcriptOnly ? 'Model untuk transkrip' : 'Model untuk memilih momen';
  document.querySelector('#analysisHelp').textContent = transcriptOnly ? 'Subtitle sumber dipakai jika tersedia. Whisper offline mengubah audio menjadi teks jika subtitle tidak tersedia. Tidak ada permintaan ke model pemilih momen.' : 'Model membaca transkrip untuk menyarankan bagian menarik. Tautan video tetap memerlukan internet meskipun modelnya offline.';
  document.querySelector('#startBtn').removeAttribute('data-i18n');
  document.querySelector('#startBtn').textContent = transcriptOnly ? 'Buat transkrip' : 'Cari momen';
  const llm = document.querySelector('#useLlm');
  if (llm) llm.checked = ai;
}

document.querySelectorAll('[data-analysis-source]').forEach(button => button.addEventListener('click', () => {
  document.querySelectorAll('[data-analysis-source]').forEach(node => {
    const on = node === button;
    node.classList.toggle('active', on);
    node.setAttribute('aria-selected', on ? 'true' : 'false');
  });
  syncAnalysisSourceUI();
}));

async function initHomeAnalysis() {
  const control = document.createElement('div');
  control.className = 'field';
  control.innerHTML = `<div id="momentModelControls"><label for="processingMode">Model pemilih momen</label><select id="processingMode"><option value="local">Offline · model di komputer</option><option value="online_ai">Online · provider & API key</option><option value="offline">Offline penuh · hanya berkas lokal</option></select></div><div id="localLlmFields" class="local-llm-controls"><label for="localModel">Model pemilih momen lokal (LLM)</label><select id="localModel"><option value="">Tanpa LLM · rekomendasi heuristik</option></select><button type="button" id="detectLocalModel" class="ghost">Cari model lokal</button><div class="model-advanced"><label for="ggufModel">Model GGUF di komputer</label><select id="ggufModel"><option value="">Pilih model GGUF</option></select><div class="gguf-actions" role="group" aria-label="Memori model GGUF"><button type="button" id="loadGguf" class="ghost gguf-load">Muat model GGUF</button><button type="button" id="stopGguf" class="ghost gguf-stop">Lepaskan dari RAM</button></div><p class="field-help">Muat untuk memakai model. Lepaskan saat selesai agar RAM kembali tersedia; berkas model tetap tersimpan.</p></div><p id="localModelStatus" role="status">Tanpa LLM, kandidat memakai pola transkrip dan aktivitas audio. Skor perlu ditinjau.</p></div>`;
  document.querySelector('#aiPanel').before(control);
  document.querySelector('.analysis-modes').hidden = true;
  const localFields = document.querySelector('#localLlmFields');
  document.querySelectorAll('[name=creationTask]').forEach(input => input.addEventListener('change', syncAnalysisSourceUI));
  document.querySelectorAll('[name=canvasPreset]').forEach(input => input.addEventListener('change', () => {
    const preset = input.value;
    $('#canvasSize').value = preset === 'letterbox' ? 'portrait' : preset;
    $('#frameFit').value = ['letterbox', 'original'].includes(preset) ? 'fit' : 'center';
    $('#canvasSizeHelp').textContent = {portrait:'Kanvas 9:16, hingga 1080 × 1920. Sumber kecil mengikuti tinggi sumber.',letterbox:'Kanvas 9:16. Seluruh frame sumber ditampilkan dengan margin hitam atau buram.',square:'Kanvas kotak 1080 × 1080.',classic:'Kanvas 4:3, 1440 × 1080.',landscape:'Kanvas landscape 1920 × 1080.',original:'Rasio sumber dipertahankan. Sisi terpanjang dibatasi 1920 piksel.'}[preset];
  }));
  document.querySelector('#processingMode').addEventListener('change', () => {
    const cloud = document.querySelector('#processingMode').value === 'online_ai';
    localFields.hidden = cloud;
    onSourceChanged();
    document.querySelectorAll('[data-analysis-source]').forEach(node => {
      const selected = (node.dataset.analysisSource === 'ai') === cloud;
      node.classList.toggle('active', selected);
      node.setAttribute('aria-selected', String(selected));
    });
    syncAnalysisSourceUI();
  });
  document.querySelector('#detectLocalModel').onclick = async () => {
    const status = document.querySelector('#localModelStatus');
    status.textContent = t('hybrid.searching');
    try {
      const data = await api('/api/local-llm/models');
      document.querySelector('#localModel').innerHTML = `<option value="">${t('hybrid.select')}</option>` + data.models.map(row => `<option value="${escapeHtml(row.id)}">${escapeHtml(row.id)}</option>`).join('');
      status.textContent = t('hybrid.found', {count:data.models.length});
    } catch (error) { status.textContent = error.message; }
  };
  try {
    const data = await api('/api/local-llm/gguf');
    document.querySelector('#ggufModel').innerHTML += data.models.map(row => `<option value="${escapeHtml(row.path)}">${escapeHtml(row.name)} · ${row.size_mb} MB${row.size_mb<=1200?' · Ringan':''}</option>`).join('');
    document.querySelector('#loadGguf').disabled = !data.runtime_available || !data.models.length;
  } catch (error) { document.querySelector('#localModelStatus').textContent = error.message; }
  document.querySelector('#loadGguf').onclick = async () => {
    const button = document.querySelector('#loadGguf'), status = document.querySelector('#localModelStatus');
    const path = document.querySelector('#ggufModel').value;
    if (!path || state.jobId) { status.textContent = t('hybrid.select'); return; }
    button.disabled = true; button.textContent = 'Memuat model…'; button.setAttribute('aria-busy','true');
    document.querySelector('#stopGguf').disabled = true;
    try {
      const started = await api('/api/local-llm/start', {method:'POST', body:JSON.stringify({path})});
      trackJob(started);
      for (;;) {
        await new Promise(resolve => setTimeout(resolve, 500));
        const job = await api(`/api/jobs/${started.id}`);
        status.textContent = job.message || job.stage;
        if (job.status === 'error' || job.status === 'cancelled') throw new Error(job.error || job.message);
        if (job.status === 'done') {
          const select = document.querySelector('#localModel');
          select.replaceChildren(new Option(job.result.model, job.result.model));
          status.textContent = job.result.model;
          break;
        }
      }
    } catch (error) { status.textContent = error.message; }
    finally { button.disabled = false; button.textContent = 'Muat model GGUF'; button.removeAttribute('aria-busy'); document.querySelector('#stopGguf').disabled = false; }
  };
  document.querySelector('#stopGguf').onclick = async () => {
    const button = document.querySelector('#stopGguf'), load = document.querySelector('#loadGguf'), status = document.querySelector('#localModelStatus');
    if (state.jobId) { status.textContent = 'Tunggu pekerjaan selesai sebelum melepas model.'; return; }
    const wasDisabled = load.disabled;
    button.disabled = true; load.disabled = true; button.textContent = 'Melepas model…'; button.setAttribute('aria-busy','true');
    try { await api('/api/local-llm/stop', {method:'POST'}); status.textContent = t('hybrid.stopped'); }
    catch (error) { status.textContent = error.message; }
    finally { button.disabled = false; load.disabled = wasDisabled; button.textContent = 'Lepaskan dari RAM'; button.removeAttribute('aria-busy'); }
  };
  document.querySelector('#localModel').onchange = async () => {
    try { await api('/api/settings', {method:'POST', body:JSON.stringify({values:{llm_model:document.querySelector('#localModel').value}})}); }
    catch (error) { document.querySelector('#localModelStatus').textContent = error.message; }
  };
  document.querySelector('#aiProvider').addEventListener('change', () => {
    homeDiscoveryGeneration++;
    document.querySelector('#aiKey').value = '';
    document.querySelector('#aiModel').innerHTML = `<option value="auto">${t('home.aiModelAuto')}</option>`;
    document.querySelector('#aiStatus').textContent = '';
    homeAiKeySaved = false;
    refreshAiKeyBadge();
  });
  const llmBox = document.querySelector('#useLlm');
  if (llmBox) llmBox.addEventListener('change', () => {
    const wantAi = llmBox.checked;
    document.querySelectorAll('[data-analysis-source]').forEach(node => {
      const on = (node.dataset.analysisSource === 'ai') === wantAi;
      node.classList.toggle('active', on);
      node.setAttribute('aria-selected', on ? 'true' : 'false');
    });
    syncAnalysisSourceUI();
  });
  document.querySelector('#aiDetect').addEventListener('click', detectHomeAiModel);
  document.querySelector('#aiKey').addEventListener('blur', () => {
    if (document.querySelector('#aiKey').value.trim() && document.querySelector('#aiProvider').value) detectHomeAiModel();
  });
  document.querySelector('#aiKey').addEventListener('input', () => { homeDiscoveryGeneration++; homeAiKeySaved = false; refreshAiKeyBadge(); });
  try {
    const [{ providers }, saved] = await Promise.all([api('/api/ai/providers'), api('/api/settings')]);
    const prov = document.querySelector('#aiProvider');
    if (saved.llm_model) {
      const option = document.createElement('option'); option.value = saved.llm_model; option.textContent = saved.llm_model;
      document.querySelector('#localModel').append(option); document.querySelector('#localModel').value = saved.llm_model;
    }
    homeProviderBases = Object.fromEntries(Object.entries(providers).map(([id, p]) => [id, p.url]));
    if (saved.ai_provider && saved.ai_base_url) homeProviderBases[saved.ai_provider] = saved.ai_base_url;
    Object.entries(providers).filter(([, p]) => p.text).forEach(([id, p]) => {
      const opt = document.createElement('option');
      opt.value = id;
      opt.textContent = p.label;
      prov.append(opt);
    });
    prov.value = saved.ai_provider || '';
    homeAiKeySaved = Boolean(saved.ai_api_key);
    refreshAiKeyBadge();
    const model = document.querySelector('#aiModel');
    if (saved.ai_model) {
      const opt = document.createElement('option');
      opt.value = saved.ai_model;
      opt.textContent = saved.ai_model + ' · tersimpan';
      model.append(opt);
      model.value = saved.ai_model;
    }
    const speed = document.querySelector('#asrSpeed');
    const current = saved.asr_model || 'whisper-small-int8';
    speed.value = current.includes('tiny') ? 'fast' : current.includes('base') ? 'balanced' : 'accurate';
  } catch (error) { /* beranda tetap bisa dipakai lokal tanpa provider */ }
  syncAnalysisSourceUI();
}

async function detectHomeAiModel() {
  const generation = ++homeDiscoveryGeneration;
  const status = document.querySelector('#aiStatus');
  const provider = document.querySelector('#aiProvider').value;
  const key = document.querySelector('#aiKey').value;
  if (!provider) { status.textContent = t('home.aiNeedProvider'); return; }
  status.textContent = t('home.aiDetecting');
  try {
    const result = await api('/api/ai/models', { method: 'POST', body: JSON.stringify({ kind: 'ai', provider, base_url: homeProviderBases[provider] || '', api_key: key, use_saved_key: !key }) });
    if (generation !== homeDiscoveryGeneration) return;
    const model = document.querySelector('#aiModel');
    model.innerHTML = `<option value="auto">${t('home.aiModelAuto')}</option>` + result.models.map(m => `<option value="${escapeHtml(m.id)}">${escapeHtml(m.label)}${m.id === result.recommended ? ' · disarankan' : ''}</option>`).join('');
    model.value = result.recommended || 'auto';
    HomeGuide.models(result);
    status.textContent = `${result.models.length} model terdeteksi. ${result.note || ''}`;
  } catch (error) { if (generation === homeDiscoveryGeneration) status.textContent = error.message; }
}


function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

// Di dalam jendela aplikasi (pywebview) tautan apa pun ikut membuka jendela
// sistem baru — itu yang terasa seperti "aplikasi kebuka lagi". Buka di
// browser luar melalui API native bila ada; di web biasa biarkan default.
function openExternalUrl(url) {
  try {
    if (window.pywebview && window.pywebview.api && window.pywebview.api.open_external) {
      window.pywebview.api.open_external(url);
      return true;
    }
  } catch { /* jatuh ke perilaku normal */ }
  return false;
}

(function guardLinkNavigation() {
  const isAppWindow = () => !!(window.pywebview && window.pywebview.api);
  window.open = (url) => {
    if (typeof url === 'string' && url && !openExternalUrl(url)) {
      location.href = url;
    }
    return null;
  };
  document.addEventListener('click', (event) => {
    if (!isAppWindow()) return;
    const link = event.target.closest && event.target.closest('a[href]');
    if (!link) return;
    const href = link.getAttribute('href') || '';
    if (link.hasAttribute('download') || new URL(link.href, location.href).pathname.startsWith('/api/media')) return;
    if (!href || href.startsWith('#') || href.startsWith('javascript:')) return;
    event.preventDefault();
    if (openExternalUrl(link.href)) return;
    const anchor = document.createElement('a');
    anchor.href = link.href;
    anchor.target = '_blank';
    anchor.rel = 'noopener noreferrer';
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
  }, true);
})();

async function confirmAction(message) {
  const dialog = document.createElement('dialog'); dialog.className = 'studio-dialog';
  dialog.innerHTML = `<h3>Hapus dari perangkat?</h3><p>${escapeHtml(message)}</p><p class="field-help">Hasil yang dipilih akan dihapus dari penyimpanan Studio ZAI. Berkas asli di luar proyek tetap aman.</p><form method="dialog" class="dialog-actions"><button class="ghost" value="cancel">Batal</button><button class="danger" value="delete">Hapus</button></form>`;
  document.body.append(dialog); dialog.showModal();
  return new Promise(resolve => dialog.addEventListener('close', () => { const yes = dialog.returnValue === 'delete'; dialog.remove(); resolve(yes); }, {once:true}));
}

function openSourceEditor() {
  const project = state.project;
  openPanel(`<div class="spread"><h3>Video sumber</h3><button class="ghost" data-close>Tutup</button></div>
    <p>${escapeHtml(project.title)}</p><video id="sourcePlayer" controls preload="metadata" src="${mediaUrl(project.source)}"></video>
    <p class="field-help">Video tersimpan di proyek. Pilih bagian mana pun tanpa mengunduh lagi. Waktu dalam detik.</p>
    <div class="grid-2"><label>Mulai<input id="sourceStart" type="number" min="0" step="0.1" value="0"></label><label>Selesai<input id="sourceEnd" type="number" step="0.1" max="${project.duration}" value="${Math.min(30,project.duration)}"></label></div>
    <div class="row"><button class="ghost" id="markIn">Tandai mulai</button><button class="ghost" id="markOut">Tandai selesai</button></div>
    <label>Kanvas<select id="sourceCanvas"><option value="portrait">Portrait 9:16</option><option value="original">Asli · rasio sumber</option><option value="square">Kotak 1:1</option><option value="landscape">Landscape 16:9</option></select></label>
    <button class="primary" id="createRange">Buat klip & edit</button>`);
  $('#markIn').onclick = () => { $('#sourceStart').value = $('#sourcePlayer').currentTime.toFixed(1); };
  $('#markOut').onclick = () => { $('#sourceEnd').value = $('#sourcePlayer').currentTime.toFixed(1); };
  $('#createRange').onclick = async () => {
    try {
      const clip = await api(`/api/projects/${project.id}/clips`, {method:'POST',body:JSON.stringify({start:Number($('#sourceStart').value),end:Number($('#sourceEnd').value),canvas:$('#sourceCanvas').value})});
      closePanel(); state.project = await api(`/api/projects/${project.id}`); renderProjectDetail(); openEditor(clip.index);
    } catch(error) {toast(error.message,'error');}
  };
}

async function createTypography() {
  const dialog = document.createElement('dialog'); dialog.className = 'studio-dialog';
  dialog.innerHTML = `<h3>Tipografi buatanmu</h3><p class="field-help">Buat satu gaya dan terapkan ke seluruh subtitle klip.</p><form id="typographyForm"><div class="dialog-fields"><label>Nama template<input name="name" required maxlength="48" value="Gaya saya"></label>
    <div class="grid-2"><label>Font<select name="font">${['Inter','Anton','Barlow Condensed','DM Serif Display','Kalam'].map(f=>`<option>${f}</option>`).join('')}</select></label><label>Ukuran relatif<input name="size" type="number" min="24" max="144" value="64"></label>
    <label>Warna teks<input name="color" type="color" value="#ffffff"></label><label>Highlight kata<input name="highlight" type="color" value="#ffe100"></label>
    <label>Warna tepi / kotak<input name="outline_color" type="color" value="#000000"></label><label>Ketebalan tepi<input name="outline" type="number" min="0" max="10" value="3"></label></div>
    <label><input name="bold" type="checkbox" checked> Tebal</label><label><input name="box" type="checkbox"> Latar kotak</label><label><input name="karaoke" type="checkbox"> Highlight kata bertiming</label>
    <p class="field-help">Template tersimpan di perangkat dan dapat dipakai di proyek berikutnya.</p></div><div class="dialog-actions"><button type="button" class="ghost" id="cancelTypography">Batal</button><button type="submit" class="primary">Simpan template</button></div></form>`;
  document.body.append(dialog); dialog.showModal();
  return new Promise(resolve=>{
    let result=null;
    dialog.onclose=()=>{dialog.remove();resolve(result);};
    dialog.querySelector('#cancelTypography').onclick=()=>dialog.close();
    dialog.querySelector('form').onsubmit=async event=>{
      event.preventDefault(); const form=event.target;
      const values=Object.fromEntries(new FormData(form));
      for(const key of ['bold','box','karaoke']) values[key]=form.elements[key].checked;
      try { result=await api('/api/subtitle-presets',{method:'POST',body:JSON.stringify(values)});dialog.close(); }
      catch(error){toast(error.message,'error');}
    };
  });
}
