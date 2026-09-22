/* ---------------------------------------------------------------------------
 * Studio ZAI — editor timeline multi-track (versi ringkas ala CapCut).
 *
 * Empat track: Video (satu item sumber), Media (overlay gambar/video),
 * Teks (template tipografi) dan Audio (musik tambahan). Bentuk data sama persis
 * dengan versi Android & core Python (lihat core/studiozai/pipeline/timeline.py)
 * supaya hasil render konsisten.
 * ------------------------------------------------------------------------- */

const StudioTimeline = (() => {
  const KINDS = ["video", "media", "text", "audio"];
  const KIND_LABEL = { video: "Video", media: "Media", text: "Teks", audio: "Audio" };
  const HANDLES = { start: "start", end: "end" };

  const clamp = (value, min, max) => Math.min(max, Math.max(min, value));

  const editor = {
    clip: null,
    timeline: null,
    selected: null, // { kind, id }
    presets: [],
    previewPath: null,
    busy: false,
    inspectorTab: "subtitles",
    templateCategory: "Pop",
    el: null,

    /* ---------------------------------------------------------------- lifecycle */

    async open(index) {
      const clip = state.project && state.project.clips.find((c) => c.index === index);
      if (!clip) return;
      this.clip = clip;
      this.previewPath = null;
      this.selected = null;
      const saved = clip.timeline && Array.isArray(clip.timeline.tracks) ? clip.timeline : null;
      this.timeline = saved ? JSON.parse(JSON.stringify(saved)) : this.defaultTimeline(clip);
      if (!this.presets.length) {
        try {
          this.presets = await api("/api/subtitle-presets");
        } catch {
          this.presets = [];
        }
      }
      this.shell();
      this.renderAll();
    },

    close() {
      if (this.el) {
        this.el.querySelectorAll("video,audio").forEach((player) => {
          player.pause();
          player.removeAttribute("src");
          player.load();
        });
        this.el.hidden = true;
      }
    },

    /** Timeline awal dari sebuah klip (satu item video + track kosong). */
    defaultTimeline(clip) {
      const end = Math.max(0.2, (clip.end || 0) - (clip.start || 0));
      return {
        version: 1,
        duration: end,
        tracks: [
          {
            id: "v1",
            kind: "video",
            name: "Video",
            items: [{
              id: "v0", start: 0, end, src: state.project.source || "",
              srcStart: clip.start || 0, type: "video", crop: clip.crop || "center",
              canvas: clip.canvas || "portrait",
            }],
          },
          { id: "m1", kind: "media", items: [] },
          { id: "t1", kind: "text", items: [] },
          { id: "a1", kind: "audio", items: [] },
        ],
      };
    },

    track(kind) {
      return this.timeline.tracks.find((t) => t.kind === kind) || null;
    },

    items(kind) {
      const track = this.track(kind);
      return track ? track.items : [];
    },

    duration() {
      let longest = 0;
      for (const track of this.timeline.tracks) {
        for (const item of track.items) longest = Math.max(longest, item.end || 0);
      }
      return longest > 0 ? longest : 1;
    },

    selectedItem() {
      if (!this.selected) return null;
      const track = this.track(this.selected.kind);
      if (!track) return null;
      return track.items.find((i) => i.id === this.selected.id) || null;
    },

    nextId(kind) {
      let count = 0;
      for (const track of this.timeline.tracks) {
        if (track.kind === kind) count += track.items.length;
      }
      return `${kind[0]}${Date.now().toString(36)}${count}`;
    },

    /* --------------------------------------------------------------------- shell */

    shell() {
      if (!this.el) {
        const el = document.createElement("div");
        el.className = "editor-overlay";
        el.hidden = true;
        document.body.appendChild(el);
        this.el = el;
      }
      this.el.innerHTML = `
        <div class="editor-shell">
          <header class="editor-head">
            <div class="editor-brand"><span>Editor video</span><strong id="tlTitle"></strong></div>
            <div class="row" style="gap:var(--s2)">
              <button class="ghost" data-tl="preview">${t("editor.previewDraft")}</button>
              <button class="ghost" data-tl="save">${t("common.save")}</button>
              <button class="primary" data-tl="render">Ekspor video</button>
              <button class="tl-close" data-tl="close" aria-label="Tutup editor" title="Tutup editor">×</button>
            </div>
          </header>
          <div class="editor-body">
            <div class="editor-stage" id="tlStage"></div>
            <aside class="editor-side" id="tlInspector"></aside>
          </div>
          <div class="editor-tools">
            <button class="ghost" data-tl="add-text">+ ${t("editor.addText")}</button>
            <button class="ghost" data-tl="add-media">+ ${t("editor.addMedia")}</button>
            <button class="ghost" data-tl="add-music">+ ${t("editor.addMusic")}</button>
            <span class="muted" id="tlHint" style="margin-left:auto"></span>
          </div>
          <div class="editor-tracks" id="tlTracks"></div>
        </div>`;
      this.el.hidden = false;

      const bind = (action, handler) => {
        const node = this.el.querySelector(`[data-tl="${action}"]`);
        if (node) node.addEventListener("click", handler);
      };
      bind("close", () => this.close());
      bind("save", () => this.save());
      bind("render", () => this.render());
      bind("preview", () => this.preview());
      bind("add-text", () => this.addText());
      bind("add-media", () => this.addMedia());
      bind("add-music", () => this.addMusic());

      const title = this.el.querySelector("#tlTitle");
      if (title) title.textContent = this.clip.title || `Klip ${(this.clip.index || 0) + 1}`;
      const hint = this.el.querySelector("#tlHint");
      if (hint) hint.textContent = t("editor.timelineHint") || "";
    },

    renderAll() {
      this.renderStage();
      this.renderTracks();
      this.renderInspector();
    },

    /* --------------------------------------------------------------------- stage */

    renderStage() {
      const stage = this.el.querySelector("#tlStage");
      if (!stage) return;
      if (this.previewPath) {
        stage.innerHTML = `<video id="tlVideo" controls src="${mediaUrl(this.previewPath)}&v=${Date.now()}"></video>`;
        return;
      }
      const thumb = this.clip.files && this.clip.files.thumb ? mediaUrl(this.clip.files.thumb) : "";
      stage.innerHTML = `
        <div class="editor-stage-inner">
          ${thumb ? `<img class="thumb" src="${thumb}" alt="" />` : ""}
          <p class="muted">${t("editor.previewDraft")}</p>
        </div>`;
    },

    /* -------------------------------------------------------------------- tracks */

    renderTracks() {
      const host = this.el.querySelector("#tlTracks");
      if (!host) return;
      const duration = this.duration();
      host.innerHTML = KINDS.map((kind) => {
        const items = this.items(kind);
        const blocks = items.map((item) => {
          const selected = this.selected && this.selected.kind === kind && this.selected.id === item.id;
          const left = (item.start / duration) * 100;
          const width = clamp(((item.end - item.start) / duration) * 100, 2, 100);
          const label = item.text ? item.text : (item.src ? item.src.split(/[\\/]/).pop() : "—");
          return `<div class="tl-block ${kind}${selected ? " selected" : ""}"
                       data-kind="${kind}" data-id="${item.id}"
                       style="left:${left}%; width:${width}%">
              <span class="tl-handle tl-handle-left" data-handle="start"></span>
              <span class="tl-label">${escapeHtml(label)}</span>
              <span class="tl-handle tl-handle-right" data-handle="end"></span>
            </div>`;
        }).join("");
        return `<div class="tl-row">
            <span class="tl-kind">${KIND_LABEL[kind]}</span>
            <div class="tl-lane" data-lane="${kind}">${blocks}</div>
          </div>`;
      }).join("");

      host.querySelectorAll(".tl-block").forEach((node) => {
        node.addEventListener("pointerdown", (event) => this.startDrag(event, node));
        node.addEventListener("dblclick", () => this.removeItem(node.dataset.kind, node.dataset.id));
      });
    },

    /** Geser (ubah waktu) atau tarik tepi (ubah durasi) sebuah blok. */
    startDrag(event, node) {
      event.preventDefault();
      const kind = node.dataset.kind;
      const item = this.items(kind).find((i) => i.id === node.dataset.id);
      if (!item) return;
      this.selected = { kind, id: item.id };
      this.inspectorTab = kind === "video" ? "clip" : "element";
      const mode = event.target.dataset.handle || "move";
      const lane = node.parentElement;
      const secondsPerPx = this.duration() / lane.getBoundingClientRect().width;
      const startX = event.clientX;
      const origin = { start: item.start, end: item.end };

      const onMove = (moveEvent) => {
        const delta = (moveEvent.clientX - startX) * secondsPerPx;
        if (mode === HANDLES.start) {
          item.start = clamp(origin.start + delta, 0, origin.end - 0.3);
        } else if (mode === HANDLES.end) {
          item.end = clamp(origin.end + delta, origin.start + 0.3, 3600);
        } else {
          const length = origin.end - origin.start;
          item.start = clamp(origin.start + delta, 0, 3600);
          item.end = item.start + length;
        }
        this.renderTracks();
        this.renderInspector();
      };
      const onUp = () => {
        document.removeEventListener("pointermove", onMove);
        document.removeEventListener("pointerup", onUp);
      };
      document.addEventListener("pointermove", onMove);
      document.addEventListener("pointerup", onUp);
      this.renderInspector();
    },

    removeItem(kind, id) {
      const track = this.track(kind);
      if (!track) return;
      if (kind === "video") {
        toast("Item video tidak bisa dihapus.", "error");
        return;
      }
      track.items = track.items.filter((item) => item.id !== id);
      if (this.selected && this.selected.id === id) this.selected = null;
      this.renderAll();
    },

    /* ---------------------------------------------------------------------- add */

    addText() {
      const track = this.track("text");
      if (!track) return;
      const item = {
        id: this.nextId("text"),
        start: 0,
        end: Math.min(3, this.duration()),
        text: "Teks baru",
        template: (this.presets[0] && this.presets[0].id) || "tiktok_pop",
        x: 0.5,
        y: 0.8,
      };
      track.items.push(item);
      this.selected = { kind: "text", id: item.id };
      this.inspectorTab = "element";
      this.renderAll();
    },

    async addMedia() {
      await this.addAssetItem("media");
    },

    async addMusic() {
      await this.addAssetItem("audio");
    },

    async addAssetItem(kind) {
      const picked = await pickAsset(kind === "audio" ? "audio" : "media");
      if (!picked) return;
      try {
        const { path: asset } = await api(`/api/projects/${state.project.id}/assets`, {
          method: "POST",
          body: JSON.stringify({ path: picked }),
        });
        const track = this.track(kind);
        if (!track) return;
        const isVideo = kind === "media" && /\.(mp4|mov|webm|mkv|m4v)$/i.test(asset);
        const item = {
          id: this.nextId(kind),
          start: 0,
          end: Math.min(kind === "audio" ? 10 : 4, this.duration()),
          src: asset,
          type: kind === "audio" ? "audio" : (isVideo ? "video" : "image"),
          scale: 0.6,
          gain: 0.6,
          x: 0.5,
          y: 0.5,
        };
        track.items.push(item);
        this.selected = { kind, id: item.id };
      this.inspectorTab = kind === "video" ? "clip" : "element";
        this.renderAll();
      } catch (error) {
        toast(error.message, "error");
      }
    },

    /* ----------------------------------------------------------------- inspector */

    presetGallery(value, attr) {
      const category = this.templateCategory;
      return `<div class="template-filters" aria-label="Kategori template">${["Semua", "Pop", "Neon", "Editorial", "Label", "Essential"].map(c => `<button data-category="${c}" class="${c === category ? 'active' : ''}">${c}</button>`).join('')}</div>
        <div class="tl-presets">${this.presets.filter(p => category === "Semua" || p.category === category).map(p => `
          <button class="tl-preset ${value === p.id ? 'active' : ''}" ${attr}="${p.id}" aria-pressed="${value === p.id}" title="${escapeHtml(p.label)}">
            <div class="preset-swatch ${p.category === 'Neon' ? 'glow' : ''}" style="--preset-color:${p.color};--preset-outline:${p.outline}"><strong style="font-family:'${p.font}';font-style:${p.italic === 'yes' ? 'italic' : 'normal'};${p.box === 'yes' ? 'background:var(--preset-outline);text-shadow:none;padding:3px 6px;' : ''}">${escapeHtml(p.sample)}</strong></div>
            <span>${escapeHtml(p.label)} <i>${value === p.id ? '✓' : '+'}</i></span>
          </button>`).join('')}</div>`;
    },

    positionPicker(item) {
      return `<div class="position-control"><label>Posisi di dalam kanvas</label><div class="position-grid">${[.18,.5,.82].flatMap((y, r) => [.18,.5,.82].map((x,c) => `<button data-position="${x},${y}" title="${['Atas','Tengah','Bawah'][r]} ${['kiri','tengah','kanan'][c]}" aria-label="${['Atas','Tengah','Bawah'][r]} ${['kiri','tengah','kanan'][c]}" class="${Math.abs(item.x-x)<.08 && Math.abs(item.y-y)<.08 ? 'active' : ''}"><span></span></button>`)).join('')}</div><div class="grid-2"><label>X (%)<input id="tlX" type="number" min="0" max="100" value="${Math.round(item.x*100)}"></label><label>Y (%)<input id="tlY" type="number" min="0" max="100" value="${Math.round(item.y*100)}"></label></div><p class="field-help">Pilih titik jangkar, atau isi persentase untuk posisi presisi.</p></div>`;
    },

    renderInspector() {
      const host = this.el.querySelector("#tlInspector");
      if (!host) return;
      const selected = this.selectedItem(), clip = this.clip;
      const base = this.items("video")[0] || {};
      const options = (values, value) => values.map(([id,label]) => `<option value="${id}" ${id === value ? 'selected' : ''}>${label}</option>`).join('');
      host.innerHTML = `<div class="inspector-tabs">${[['clip','Klip'],['subtitles','Subtitle'],['element','Elemen']].map(([id,label]) => `<button data-inspector="${id}" class="${this.inspectorTab === id ? 'active' : ''}">${label}</button>`).join('')}</div>
        <section class="inspector-section" ${this.inspectorTab !== 'clip' ? 'hidden' : ''}>
          <h3>Video & audio</h3>
          <label>Ukuran video<select id="tlCanvas">${options([['original','Asli · pertahankan rasio'],['portrait','Portrait · 9:16'],['square','Kotak · 1:1'],['landscape','Landscape · 16:9']],base.canvas)}</select></label>
          <label>Penyesuaian gambar<select id="tlCrop">${options([['fit','Fit · tampilkan seluruh gambar'],['center','Isi kanvas · potong tengah'],['blur','Isi latar dengan blur'],['none','Letterbox · bilah hitam']],base.crop)}</select></label>
          <p class="field-help">Fit mempertahankan seluruh gambar. Ukuran asli mengikuti rasio video sumber.</p>
          <div class="grid-2"><label>Mulai (detik)<input type="number" step="0.1" id="tlClipStart" value="${clip.start}"></label><label>Selesai (detik)<input type="number" step="0.1" id="tlClipEnd" value="${clip.end}"></label></div>
          <label>Audio<select id="tlAudio">${options([['original','Suara asli video'],['voice','Ganti dengan narasi'],['mix','Campur suara & narasi']],clip.audio_mode)}</select></label>
          <label>Naskah narasi<textarea id="tlNarration" rows="3" placeholder="Tulis kalimat untuk sulih suara…"></textarea></label><button class="ghost" data-tl-clip="tts">Buat suara dari teks</button>
        </section>
        <section class="inspector-section" ${this.inspectorTab !== 'subtitles' ? 'hidden' : ''}>
          <h3>Gaya subtitle</h3><p class="field-help">${this.presets.length} gaya untuk semua subtitle. Pilih, lalu klik Pratinjau cepat untuk melihat hasilnya.</p>
          <button class="caption-generate" data-tl="captions">Buat subtitle otomatis</button>
          ${this.presetGallery(clip.subtitle_preset, 'data-preset')}
          <details><summary>Edit teks & waktu · ${(clip.captions || []).length} baris</summary><p class="field-help">Transkrip adalah teks ucapan. Subtitle mengatur kapan teks tampil. Format: mulai|selesai|teks dalam detik.</p><textarea id="tlCaptions" rows="7">${escapeHtml(captionsToText(clip.captions))}</textarea></details>
        </section>
        <section class="inspector-section" ${this.inspectorTab !== 'element' ? 'hidden' : ''}>
          <h3>Pengaturan elemen</h3>
          ${selected && this.selected.kind !== 'video' ? `
            ${this.selected.kind === 'text' ? `<label>Teks overlay<textarea id="tlText" rows="3">${escapeHtml(selected.text || '')}</textarea></label>${this.presetGallery(selected.template, 'data-item-preset')}` : ''}
            ${['text','media'].includes(this.selected.kind) ? this.positionPicker(selected) : ''}
            ${this.selected.kind === 'media' ? `<label>Ukuran (%)<input type="number" id="tlScale" min="5" max="100" value="${Math.round(selected.scale*100)}"></label>` : ''}
            ${this.selected.kind === 'audio' ? `<label>Volume (%)<input type="number" id="tlGain" min="0" max="200" value="${Math.round(selected.gain*100)}"></label>` : ''}
            <div class="grid-2"><label>Mulai (detik)<input type="number" step="0.1" id="tlItemStart" value="${selected.start}"></label><label>Selesai (detik)<input type="number" step="0.1" id="tlItemEnd" value="${selected.end}"></label></div><button class="ghost danger" data-tl-item="delete">Hapus elemen</button>
          ` : '<div class="empty">Pilih elemen di timeline, atau tambahkan teks, media, dan musik melalui tombol di bawah pratinjau.</div>'}
        </section>`;
      this.bindInspector();
    },

    bindInspector() {
      const host = this.el.querySelector("#tlInspector");
      const selected = this.selectedItem();
      host.querySelectorAll('[data-inspector]').forEach(node => node.addEventListener('click', () => { this.inspectorTab = node.dataset.inspector; this.renderInspector(); }));
      host.querySelectorAll('[data-category]').forEach(node => node.addEventListener('click', () => { this.templateCategory = node.dataset.category; this.renderInspector(); }));
      host.querySelectorAll('[data-position]').forEach(node => node.addEventListener('click', () => { if (selected) { [selected.x, selected.y] = node.dataset.position.split(',').map(Number); this.renderInspector(); } }));
      host.querySelector('[data-tl="captions"]').addEventListener("click", () => this.generateCaptions());

      const clipStart = host.querySelector("#tlClipStart");
      const clipEnd = host.querySelector("#tlClipEnd");
      const updateTrim = () => {
        this.clip.start = Math.max(0, Number(clipStart.value) || 0);
        this.clip.end = Math.max(this.clip.start + 0.2, Number(clipEnd.value) || 0);
        const base = this.items("video")[0];
        if (base) { base.srcStart = this.clip.start; base.start = 0; base.end = this.clip.end - this.clip.start; }
        this.renderTracks();
      };
      if (clipStart) clipStart.addEventListener("change", updateTrim);
      if (clipEnd) clipEnd.addEventListener("change", updateTrim);

      const videoItem = this.items("video")[0];
      const crop = host.querySelector("#tlCrop");
      if (crop && videoItem) crop.addEventListener("change", () => { videoItem.crop = crop.value; this.renderTracks(); });
      const canvas = host.querySelector("#tlCanvas");
      if (canvas && videoItem) canvas.addEventListener("change", () => { videoItem.canvas = canvas.value; });

      const audio = host.querySelector("#tlAudio");
      if (audio) audio.addEventListener("change", () => { this.clip.audio_mode = audio.value; });

      host.querySelectorAll("[data-preset]").forEach((node) =>
        node.addEventListener("click", () => {
          this.clip.subtitle_preset = node.dataset.preset;
          this.renderInspector();
        })
      );

      const captions = host.querySelector("#tlCaptions");
      if (captions) captions.addEventListener("input", () => {
        this.clip.captions = textToCaptions(captions.value);
      });

      const narration = host.querySelector("#tlNarration");
      const tts = host.querySelector('[data-tl-clip="tts"]');
      if (tts) tts.addEventListener("click", async () => {
        const text = (narration && narration.value ? narration.value : "").trim();
        if (!text) return toast(t("voice.text"), "error");
        try {
          const job = await api(`/api/projects/${state.project.id}/tts`, {
            method: "POST",
            body: JSON.stringify({ text, lang: state.project.language || "id", clip: this.clip.index }),
          });
          trackJob(job);
        } catch (error) {
          toast(error.message, "error");
        }
      });

      if (!selected) return;

      host.querySelectorAll("[data-item-preset]").forEach((node) =>
        node.addEventListener("click", () => {
          selected.template = node.dataset.itemPreset;
          this.renderInspector();
        })
      );

      const text = host.querySelector("#tlText");
      if (text) text.addEventListener("input", () => { selected.text = text.value; this.renderTracks(); });

      const slider = (id, apply) => {
        const node = host.querySelector(`#${id}`);
        if (!node) return;
        node.addEventListener("input", () => {
          apply(Number(node.value) / 100);
          this.renderTracks();
          const label = node.previousElementSibling;
          if (label) {
            const value = label.querySelector("span");
            if (value) value.textContent = Number(node.value).toFixed(2);
          }
        });
      };
      slider("tlX", (value) => { selected.x = clamp(value, 0, 1); });
      slider("tlY", (value) => { selected.y = clamp(value, 0, 1); });
      slider("tlScale", (value) => { selected.scale = clamp(value, .05, 1); });
      slider("tlGain", (value) => { selected.gain = clamp(value, 0, 2); });

      const itemStart = host.querySelector("#tlItemStart");
      const itemEnd = host.querySelector("#tlItemEnd");
      if (itemStart) itemStart.addEventListener("change", () => {
        selected.start = Math.max(0, Number(itemStart.value) || 0);
        this.renderTracks();
      });
      if (itemEnd) itemEnd.addEventListener("change", () => {
        selected.end = Math.max(selected.start + 0.3, Number(itemEnd.value) || 0);
        this.renderTracks();
      });

      const remove = host.querySelector('[data-tl-item="delete"]');
      if (remove) remove.addEventListener("click", () => this.removeItem(this.selected.kind, selected.id));
    },

    /* ------------------------------------------------------------------ actions */

    async generateCaptions() {
      if (this.busy) return;
      this.busy = true;
      try {
        await this.save();
        toast("Membuat subtitle dari audio sumber…");
        const job = await api(`/api/projects/${state.project.id}/clips/${this.clip.index}/captions`, { method: "POST" });
        const result = await waitJob(job.id);
        this.clip.captions = result.captions || [];
        this.clip.subtitle_position = "bottom";
        this.renderInspector();
        toast(this.clip.captions.length ? "Subtitle siap. Pilih tipografi lalu Pratinjau atau Render." : "Tidak ada ucapan terdeteksi.");
      } catch (error) { toast(error.message, "error"); }
      finally { this.busy = false; }
    },

    /** Simpan timeline + field turunan (crop/kanvas/trim) ke proyek. */
    async save() {
      const videoItem = this.items("video")[0];
      const payload = {
        timeline: this.timeline,
        subtitle_preset: this.clip.subtitle_preset,
        subtitle_position: this.clip.subtitle_position,
        audio_mode: this.clip.audio_mode,
        captions: this.clip.captions,
        start: this.clip.start,
        end: this.clip.end,
      };
      if (videoItem) {
        payload.crop = videoItem.crop;
        payload.canvas = videoItem.canvas;
      }
      await api(`/api/projects/${state.project.id}/clips/${this.clip.index}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
      state.project = await api(`/api/projects/${state.project.id}`);
      this.clip = state.project.clips.find((c) => c.index === this.clip.index) || this.clip;
      toast(t("toast.saved"));
      renderProjectDetail();
    },

    async preview() {
      if (this.busy) return;
      this.el.querySelectorAll('video').forEach(v => { v.pause(); v.removeAttribute('src'); v.load(); });
      this.el.querySelector('#tlStage').innerHTML = '<div class="editor-stage-inner"><div class="spinner"></div><p>Menyusun pratinjau…</p></div>';
      this.busy = true;
      try {
        await this.save();
        const job = await api(`/api/projects/${state.project.id}/clips/${this.clip.index}/preview`, { method: "POST" });
        const result = await waitJob(job.id);
        if (result && result.mp4) {
          this.previewPath = result.mp4;
          if (!this.el.hidden) this.renderStage();
        }
      } catch (error) {
        toast(error.message, "error");
      } finally {
        this.busy = false;
      }
    },

    async render() {
      if (this.busy) return;
      this.busy = true;
      try {
        await this.save();
        const job = await api(`/api/projects/${state.project.id}/clips/${this.clip.index}/render`, { method: "POST" });
        trackJob(job);
        this.close();
      } catch (error) {
        toast(error.message, "error");
      } finally {
        this.busy = false;
      }
    },
  };

  /* ------------------------------------------------------------------- helpers */

  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  /** Poll job sampai selesai; mengembalikan job.result. */
  async function waitJob(jobId) {
    for (let attempt = 0; attempt < 900; attempt++) {
      const job = await api(`/api/jobs/${jobId}`);
      if (job.status === "done") return job.result || {};
      if (job.status === "error" || job.status === "cancelled") {
        throw new Error(job.error || job.message || "pekerjaan gagal");
      }
      await new Promise((resolve) => setTimeout(resolve, 700));
    }
    throw new Error("pekerjaan terlalu lama");
  }

  /** Pilih berkas media: dialog native (pywebview) atau input file di browser. */
  async function pickAsset(kind) {
    if (window.pywebview && window.pywebview.api && window.pywebview.api.pick_file) {
      return window.pywebview.api.pick_file();
    }
    return new Promise((resolve) => {
      const input = document.createElement("input");
      input.type = "file";
      input.accept = kind === "audio" ? "audio/*" : "video/*,image/*";
      input.onchange = () => resolve(input.files[0] ? input.files[0].name : null);
      input.click();
    });
  }

  return {
    open: (index) => editor.open(index),
    close: () => editor.close(),
  };
})();
