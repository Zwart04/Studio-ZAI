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
      if (this.el) this.el.hidden = true;
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
            <strong id="tlTitle"></strong>
            <div class="row" style="gap:var(--s2)">
              <button class="ghost" data-tl="preview">${t("editor.previewDraft")}</button>
              <button class="primary" data-tl="save">${t("common.save")}</button>
              <button class="ghost" data-tl="render">${t("common.render")}</button>
              <button class="mini" data-tl="close">${t("common.close")}</button>
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
        stage.innerHTML = `<video id="tlVideo" controls autoplay src="${mediaUrl(this.previewPath)}"></video>`;
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
        this.renderAll();
      } catch (error) {
        toast(error.message, "error");
      }
    },

    /* ----------------------------------------------------------------- inspector */

    renderInspector() {
      const host = this.el.querySelector("#tlInspector");
      if (!host) return;
      const selected = this.selectedItem();
      const clip = this.clip;
      const videoItem = this.items("video")[0] || null;
      const parts = [];

      parts.push(`<div class="stack" style="gap:var(--s4)">
        <div>
          <label>${t("editor.trim")} — mulai / selesai (s)</label>
          <div class="row" style="gap:var(--s2)">
            <input type="number" step="0.1" id="tlClipStart" value="${clip.start}" />
            <input type="number" step="0.1" id="tlClipEnd" value="${clip.end}" />
          </div>
        </div>`);

      if (videoItem) {
        parts.push(`
        <div>
          <label>${t("editor.crop")}</label>
          <select id="tlCrop">
            ${["center", "blur", "fit", "none"].map((mode) => {
              const label = { center: "Center 9:16", blur: "Blur background", fit: "Fit (tidak memotong)", none: "Letterbox" }[mode];
              return `<option value="${mode}" ${videoItem.crop === mode ? "selected" : ""}>${label}</option>`;
            }).join("")}
          </select>
          <p class="muted" style="margin:6px 0 0">${t("editor.trimHint") || ""}</p>
        </div>
        <div>
          <label>Ukuran klip</label>
          <select id="tlCanvas">
            <option value="portrait" ${videoItem.canvas === "portrait" ? "selected" : ""}>Potrait 9:16 (TikTok/Reels)</option>
            <option value="original" ${videoItem.canvas === "original" ? "selected" : ""}>Ukuran asli video</option>
            <option value="square" ${videoItem.canvas === "square" ? "selected" : ""}>Kotak 1:1</option>
            <option value="landscape" ${videoItem.canvas === "landscape" ? "selected" : ""}>Landscape 16:9</option>
          </select>
        </div>`);
      }

      parts.push(`
        <div>
          <label>${t("editor.audio")}</label>
          <select id="tlAudio">
            <option value="original" ${clip.audio_mode === "original" ? "selected" : ""}>${t("audio.original")}</option>
            <option value="voice" ${clip.audio_mode === "voice" ? "selected" : ""}>${t("audio.voice")}</option>
            <option value="mix" ${clip.audio_mode === "mix" ? "selected" : ""}>${t("audio.mix")}</option>
          </select>
        </div>`);

      parts.push(`<div>
          <label>${t("editor.style")}</label>
          <div class="tl-presets">
            ${this.presets.map((preset) => `
              <button class="tl-preset ${clip.subtitle_preset === preset.id ? "active" : ""}" data-preset="${preset.id}">
                <strong>Aa</strong><span>${escapeHtml(preset.label)}</span>
              </button>`).join("")}
          </div>
        </div>
        <div>
          <label>${t("editor.captions")}</label>
          <textarea id="tlCaptions" rows="6">${escapeHtml(captionsToText(clip.captions))}</textarea>
        </div>
        <div>
          <label>${t("editor.narration")}</label>
          <textarea id="tlNarration" rows="2" placeholder="Teks narasi…"></textarea>
          <button class="ghost" data-tl-clip="tts" style="margin-top:8px">${t("editor.ttsClip")}</button>
        </div>`);

      if (selected) {
        parts.push(`<hr class="tl-sep" />`);
        const kind = this.selected.kind;
        if (kind === "text") {
          parts.push(`
            <div>
              <label>Teks</label>
              <textarea id="tlText" rows="3">${escapeHtml(selected.text || "")}</textarea>
            </div>
            <div>
              <label>${t("editor.template")}</label>
              <div class="tl-presets">
                ${this.presets.map((preset) => `
                  <button class="tl-preset ${selected.template === preset.id ? "active" : ""}" data-item-preset="${preset.id}">
                    <strong>Aa</strong><span>${escapeHtml(preset.label)}</span>
                  </button>`).join("")}
              </div>
            </div>
            <div><label>Posisi X <span class="muted">${selected.x.toFixed(2)}</span></label>
              <input type="range" min="0" max="1" step="0.01" id="tlX" value="${selected.x}" /></div>
            <div><label>Posisi Y <span class="muted">${selected.y.toFixed(2)}</span></label>
              <input type="range" min="0" max="1" step="0.01" id="tlY" value="${selected.y}" /></div>`);
        }
        if (kind === "media") {
          parts.push(`
            <div><label>Ukuran <span class="muted">${selected.scale.toFixed(2)}</span></label>
              <input type="range" min="0.1" max="1" step="0.01" id="tlScale" value="${selected.scale}" /></div>
            <div><label>Posisi X <span class="muted">${selected.x.toFixed(2)}</span></label>
              <input type="range" min="0" max="1" step="0.01" id="tlX" value="${selected.x}" /></div>
            <div><label>Posisi Y <span class="muted">${selected.y.toFixed(2)}</span></label>
              <input type="range" min="0" max="1" step="0.01" id="tlY" value="${selected.y}" /></div>`);
        }
        if (kind === "audio") {
          parts.push(`
            <div><label>Volume <span class="muted">${selected.gain.toFixed(2)}</span></label>
              <input type="range" min="0" max="2" step="0.05" id="tlGain" value="${selected.gain}" /></div>`);
        }
        parts.push(`
          <div>
            <label>Waktu item (mulai / selesai)</label>
            <div class="row" style="gap:var(--s2)">
              <input type="number" step="0.1" id="tlItemStart" value="${selected.start.toFixed(2)}" />
              <input type="number" step="0.1" id="tlItemEnd" value="${selected.end.toFixed(2)}" />
            </div>
          </div>
          <button class="ghost" data-tl-item="delete" style="color:var(--red)">${t("editor.deleteItem")}</button>`);
      }

      parts.push(`</div>`);
      host.innerHTML = parts.join("");
      this.bindInspector();
    },

    bindInspector() {
      const host = this.el.querySelector("#tlInspector");
      const selected = this.selectedItem();

      const clipStart = host.querySelector("#tlClipStart");
      const clipEnd = host.querySelector("#tlClipEnd");
      if (clipStart) clipStart.addEventListener("change", () => { this.clip.start = Number(clipStart.value) || 0; });
      if (clipEnd) clipEnd.addEventListener("change", () => { this.clip.end = Number(clipEnd.value) || this.clip.start + 1; });

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
      if (captions) captions.addEventListener("change", () => {
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
          apply(Number(node.value));
          this.renderTracks();
          const label = node.previousElementSibling;
          if (label) {
            const value = label.querySelector("span");
            if (value) value.textContent = Number(node.value).toFixed(2);
          }
        });
      };
      slider("tlX", (value) => { selected.x = value; });
      slider("tlY", (value) => { selected.y = value; });
      slider("tlScale", (value) => { selected.scale = value; });
      slider("tlGain", (value) => { selected.gain = value; });

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

    /** Simpan timeline + field turunan (crop/kanvas/trim) ke proyek. */
    async save() {
      const videoItem = this.items("video")[0];
      const payload = {
        timeline: this.timeline,
        subtitle_preset: this.clip.subtitle_preset,
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
      this.busy = true;
      try {
        await this.save();
        const job = await api(`/api/projects/${state.project.id}/clips/${this.clip.index}/preview`, { method: "POST" });
        const result = await waitJob(job.id);
        if (result && result.mp4) {
          this.previewPath = result.mp4;
          this.renderStage();
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
