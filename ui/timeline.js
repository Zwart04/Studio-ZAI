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
    previewBusy: false,
    previewTimer: null,
    changeTimer: null,
    generation: 0,
    previewFingerprint: "",
    playhead: 0,
    inspectorTab: "subtitles",
    templateCategory: "Pop",
    el: null,

    /* ---------------------------------------------------------------- lifecycle */

    async open(index) {
      const clip = state.project && state.project.clips.find((c) => c.index === index);
      if (!clip) return;
      this.close();
      this.clip = clip;
      this.previewPath = clip.files?.mp4 || null;
      this.playhead = 0;
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
      this.previewFingerprint = this.fingerprint();
      this.schedulePreview();
      this.changeTimer = setInterval(() => {
        const fingerprint = this.fingerprint();
        if (fingerprint !== this.previewFingerprint) {
          this.previewFingerprint = fingerprint;
          this.schedulePreview();
        }
      }, 350);
    },

    fingerprint() {
      return JSON.stringify([this.timeline, this.clip.start, this.clip.end,
        this.clip.captions, this.clip.subtitle_preset, this.clip.subtitle_position, this.clip.audio_mode]);
    },

    schedulePreview() {
      clearTimeout(this.previewTimer);
      this.previewTimer = setTimeout(() => this.preview(), 900);
    },

    close() {
      clearInterval(this.changeTimer);
      clearTimeout(this.previewTimer);
      this.generation++;
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
      // The source video defines the visible/exported timeline. Overlays cannot
      // extend the movie and should not make the ruler jump while being dragged.
      const base = this.items("video")[0];
      return Math.max(0.2, Number(base?.end || 0) - Number(base?.start || 0));
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
              <button class="ghost" data-tl="save">${t("common.save")}</button>
              <button class="primary" data-tl="render">Ekspor video</button>
              <button class="tl-close" data-tl="close" aria-label="Tutup editor" title="Tutup editor">×</button>
            </div>
          </header>
          <div class="editor-body">
            <div class="editor-stage" id="tlStage"></div>
            <aside class="editor-side" id="tlInspector"></aside>
          </div>
          <section class="editor-timeline" aria-label="Timeline editor">
            <div class="editor-tools">
              <div class="timeline-heading"><strong>${t("editor.timeline")}</strong><span id="tlTimeReadout">00:00 / 00:00</span></div>
              <div class="timeline-add-actions">
                <button class="ghost" data-tl="add-text" draggable="true" data-drag-kind="text" title="Klik untuk menambah di posisi pemutar, atau seret ke track Teks">＋ ${t("editor.addText")}</button>
                <button class="ghost" data-tl="add-media" draggable="true" data-drag-kind="media" title="Klik untuk memilih berkas, atau seret ke track Media">＋ ${t("editor.addMedia")}</button>
                <button class="ghost" data-tl="add-music" draggable="true" data-drag-kind="audio" title="Klik untuk memilih berkas, atau seret ke track Audio">＋ ${t("editor.addMusic")}</button>
              </div>
            </div>
            <div class="timeline-scroll"><div class="editor-tracks" id="tlTracks"></div></div>
            <p class="timeline-hint" id="tlHint"></p>
          </section>
        </div>`;
      this.el.hidden = false;

      const bind = (action, handler) => {
        const node = this.el.querySelector(`[data-tl="${action}"]`);
        if (node) node.addEventListener("click", handler);
      };
      bind("close", () => this.close());
      bind("save", () => this.save());
      bind("render", () => this.render());
      bind("add-text", () => this.addText());
      bind("add-media", () => this.addMedia());
      bind("add-music", () => this.addMusic());

      this.el.querySelectorAll('[data-drag-kind]').forEach((node) => {
        node.addEventListener('dragstart', (event) => {
          event.dataTransfer.effectAllowed = 'copy';
          event.dataTransfer.setData('application/x-studiozai-kind', node.dataset.dragKind);
          event.dataTransfer.setData('text/plain', node.dataset.dragKind);
        });
      });

      const title = this.el.querySelector("#tlTitle");
      if (title) title.textContent = this.clip.title || `Klip ${(this.clip.index || 0) + 1}`;
      const hint = this.el.querySelector("#tlHint");
      if (hint) hint.textContent = 'Klik penggaris untuk memutar dari titik tertentu. Seret blok untuk memindahkan, tepinya untuk memangkas; seret berkas gambar/video/audio ke track yang sesuai.';
      this.updatePlayhead();
    },

    renderAll() {
      this.renderStage();
      this.renderTracks();
      this.renderInspector();
    },

    /* --------------------------------------------------------------------- stage */

    renderStage(position = this.playhead, playing = false) {
      const stage = this.el.querySelector("#tlStage");
      if (!stage) return;
      const path = this.previewPath || state.project.source;
      const sourceStart = this.previewPath ? 0 : this.clip.start;
      stage.querySelectorAll('video').forEach(v => v.pause());
      stage.innerHTML = `<video id="tlVideo" controls playsinline preload="auto" data-source-start="${sourceStart}" src="${mediaUrl(path)}&v=${Date.now()}"></video><span class="preview-status" id="tlPreviewStatus" role="status"></span>`;
      const player = stage.querySelector('video');
      player.addEventListener('loadedmetadata', () => {
        player.currentTime = Math.min(sourceStart + clamp(position, 0, this.duration()), Math.max(0, player.duration - .05));
        if (playing) player.play().catch(() => {});
      }, {once:true});
      player.addEventListener('timeupdate', () => {
        this.playhead = clamp(player.currentTime - sourceStart, 0, this.duration());
        this.updatePlayhead();
      });
      if (!this.previewPath) player.addEventListener('timeupdate', () => {
        if (player.currentTime < sourceStart) player.currentTime = sourceStart;
        if (player.currentTime >= this.clip.end) { player.pause(); player.currentTime = sourceStart; }
      });
    },

    /* -------------------------------------------------------------------- tracks */

    timeLabel(seconds) {
      const total = Math.max(0, Math.floor(seconds || 0));
      return `${String(Math.floor(total / 60)).padStart(2, '0')}:${String(total % 60).padStart(2, '0')}`;
    },

    updatePlayhead() {
      if (!this.el) return;
      const duration = this.duration();
      this.playhead = clamp(this.playhead, 0, duration);
      const host = this.el.querySelector('#tlTracks');
      if (host) host.style.setProperty('--playhead-pct', `${this.playhead / duration * 100}%`);
      const readout = this.el.querySelector('#tlTimeReadout');
      if (readout) readout.textContent = `${this.timeLabel(this.playhead)} / ${this.timeLabel(duration)}`;
    },

    seek(position) {
      this.playhead = clamp(position, 0, this.duration());
      const player = this.el.querySelector('#tlVideo');
      if (player && Number.isFinite(player.duration)) {
        player.currentTime = Number(player.dataset.sourceStart || 0) + this.playhead;
      }
      this.updatePlayhead();
    },

    renderTracks() {
      const host = this.el.querySelector("#tlTracks");
      if (!host) return;
      const duration = this.duration();
      const ruler = `<div class="tl-row tl-ruler-row"><span class="tl-kind">Waktu</span><div class="tl-ruler" aria-label="Penggaris waktu · klik untuk mencari posisi">${[0, .25, .5, .75, 1].map(fraction => `<span class="tl-tick" style="left:${fraction * 100}%">${this.timeLabel(duration * fraction)}</span>`).join('')}<span class="tl-playhead" aria-hidden="true"></span></div></div>`;
      host.innerHTML = ruler + KINDS.map((kind) => {
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
            <div class="tl-lane" data-lane="${kind}" aria-label="Track ${KIND_LABEL[kind]}">${blocks}<span class="tl-playhead" aria-hidden="true"></span></div>
          </div>`;
      }).join("");

      host.querySelectorAll('.tl-ruler, .tl-lane').forEach((lane) => {
        lane.addEventListener('click', (event) => {
          if (event.target.closest('.tl-block')) return;
          const bounds = lane.getBoundingClientRect();
          this.seek((event.clientX - bounds.left) / bounds.width * duration);
        });
      });
      host.querySelectorAll('.tl-lane').forEach((lane) => {
        const kind = lane.dataset.lane;
        lane.addEventListener('dragover', (event) => {
          const types = Array.from(event.dataTransfer.types || []);
          const isFile = types.includes('Files');
          const isTool = types.includes('application/x-studiozai-kind');
          if (isTool || (isFile && ['media', 'audio'].includes(kind))) {
            event.preventDefault();
            event.dataTransfer.dropEffect = 'copy';
            lane.classList.add('drop-ready');
          }
        });
        lane.addEventListener('dragleave', () => lane.classList.remove('drop-ready'));
        lane.addEventListener('drop', async (event) => {
          lane.classList.remove('drop-ready');
          const dragged = event.dataTransfer.getData('application/x-studiozai-kind');
          const file = event.dataTransfer.files?.[0];
          if (dragged !== kind && !(file && ['media', 'audio'].includes(kind))) return;
          event.preventDefault();
          const bounds = lane.getBoundingClientRect();
          const at = clamp((event.clientX - bounds.left) / bounds.width * this.duration(), 0, this.duration() - 0.2);
          if (file) {
            await this.addDroppedFile(kind, file, at);
          } else if (kind === 'text') {
            this.addText(at);
          } else {
            await this.addAssetItem(kind, at);
          }
        });
      });

      host.querySelectorAll(".tl-block").forEach((node) => {
        node.addEventListener("pointerdown", (event) => this.startDrag(event, node));
        node.addEventListener("dblclick", () => this.removeItem(node.dataset.kind, node.dataset.id));
      });
      this.updatePlayhead();
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
      const timelineDuration = this.duration();
      const origin = { start: item.start, end: item.end, srcStart: item.srcStart || 0, captions: JSON.parse(JSON.stringify(this.clip.captions || [])), framing: JSON.parse(JSON.stringify(item.framing || {})), variants: JSON.parse(JSON.stringify(this.clip.caption_variants || {})) };
      this.seek(origin.start);

      const onMove = (moveEvent) => {
        const delta = (moveEvent.clientX - startX) * secondsPerPx;
        if (mode === HANDLES.start) {
          item.start = clamp(origin.start + delta, 0, origin.end - 0.3);
        } else if (mode === HANDLES.end) {
          const maxEnd = kind === 'video' ? Math.max(origin.start + .3, state.project.duration - origin.srcStart) : timelineDuration;
          item.end = clamp(origin.end + delta, origin.start + 0.3, maxEnd);
        } else {
          const length = origin.end - origin.start;
          item.start = clamp(origin.start + delta, 0, Math.max(0, timelineDuration - length));
          item.end = item.start + length;
        }
        if (kind === 'video') {
          if (mode === 'move') { item.start=origin.start;item.end=origin.end; }
          const delta=item.start-origin.start;
          item.srcStart=origin.srcStart+delta;
          item.end=Math.min(item.end-item.start,state.project.duration-item.srcStart);item.start=0;
          this.clip.start=item.srcStart;this.clip.end=item.srcStart+item.end;
          const shift=rows=>rows.filter(c=>c.end>delta && c.start<delta+item.end).map(c=>({...c,start:Math.max(0,c.start-delta),end:Math.min(item.end,c.end-delta),...(c.words?{words:shift(c.words)}:{})}));
          this.clip.captions=shift(origin.captions);
          this.clip.caption_variants=Object.fromEntries(Object.entries(origin.variants).map(([lang,rows])=>[lang,shift(rows)]));
          item.framing=CreatorEditor.shiftFraming(origin.framing,delta,item.end);
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

    addText(at = this.playhead) {
      const track = this.track("text");
      if (!track) return;
      const start = clamp(at, 0, Math.max(0, this.duration() - .3));
      const item = {
        id: this.nextId("text"),
        start,
        end: Math.min(start + 3, this.duration()),
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
      await this.addAssetItem("media", this.playhead);
    },

    async addMusic() {
      await this.addAssetItem("audio", this.playhead);
    },

    async uploadFile(file) {
      const response = await fetch(`/api/projects/${state.project.id}/assets/upload`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/octet-stream', 'X-Filename': encodeURIComponent(file.name) },
        body: file,
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || `Impor berkas gagal (${response.status})`);
      }
      const { path } = await response.json();
      return path;
    },

    async addDroppedFile(kind, file, at) {
      const extension = file.name.split('.').pop()?.toLowerCase() || '';
      const isAudio = file.type.startsWith('audio/') || ['wav','mp3','m4a','flac','aac','ogg','opus','wma','aif','aiff'].includes(extension);
      const isMedia = file.type.startsWith('image/') || file.type.startsWith('video/') || ['mp4','mov','webm','mkv','m4v','avi','jpg','jpeg','png','webp','gif','bmp'].includes(extension);
      if ((kind === 'audio' && !isAudio) || (kind === 'media' && !isMedia)) {
        toast(kind === 'audio' ? 'Seret berkas audio ke track Audio.' : 'Seret gambar atau video ke track Media.', 'error');
        return;
      }
      try {
        const path = await this.uploadFile(file);
        await this.addAssetItem(kind, at, path);
      } catch (error) { toast(error.message, 'error'); }
    },

    async addAssetItem(kind, at = this.playhead, uploadedPath = null) {
      try {
        let asset = uploadedPath;
        if (!asset) {
          const picked = await pickAsset(kind === "audio" ? "audio" : "media");
          if (!picked) return;
          if (picked instanceof File) {
            asset = await this.uploadFile(picked);
          } else {
            const result = await api(`/api/projects/${state.project.id}/assets`, {
              method: "POST", body: JSON.stringify({ path: picked }),
            });
            asset = result.path;
          }
        }
        const track = this.track(kind);
        if (!track) return;
        const isVideo = kind === "media" && /\.(mp4|mov|webm|mkv|m4v|avi)$/i.test(asset);
        const start = clamp(at, 0, Math.max(0, this.duration() - .3));
        const item = {
          id: this.nextId(kind),
          start,
          end: Math.min(start + (kind === "audio" ? 10 : 4), this.duration()),
          src: asset,
          type: kind === "audio" ? "audio" : (isVideo ? "video" : "image"),
          scale: 0.6,
          gain: 0.6,
          x: 0.5,
          y: 0.5,
        };
        track.items.push(item);
        this.selected = { kind, id: item.id };
        this.inspectorTab = "element";
        this.renderAll();
      } catch (error) {
        toast(error.message, "error");
      }
    },

    /* ----------------------------------------------------------------- inspector */

    presetGallery(value, attr) {
      const category = this.templateCategory;
      return `<div class="template-filters" aria-label="Kategori template">${["Semua", "Pop", "Neon", "Editorial", "Label", "Essential", "Custom"].map(c => `<button data-category="${c}" class="${c === category ? 'active' : ''}">${c}</button>`).join('')}</div>
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
          <h3>Video & audio</h3><label>Judul / hook<input id="tlHook" value="${escapeHtml(clip.title || '')}"></label><button class="ghost" data-creator="crop">Atur crop & keyframe</button><button data-tl="split" class="ghost">Pisahkan klip di posisi pemutar</button>
          <label>Ukuran video<select id="tlCanvas">${options([['original','Asli · pertahankan rasio'],['portrait','Portrait · 9:16'],['square','Kotak · 1:1'],['landscape','Landscape · 16:9']],base.canvas)}</select></label>
          <label>Penyesuaian gambar<select id="tlCrop">${options([['manual','Manual · keyframe'],['fit','Fit · tampilkan seluruh gambar'],['center','Isi kanvas · potong tengah'],['blur','Isi latar dengan blur'],['none','Letterbox · bilah hitam']],base.crop)}</select></label>
          <p class="field-help">Fit mempertahankan seluruh gambar. Ukuran asli mengikuti rasio video sumber.</p>
          <div class="grid-2"><label>Mulai (detik)<input type="number" step="0.1" id="tlClipStart" value="${clip.start}"></label><label>Selesai (detik)<input type="number" step="0.1" id="tlClipEnd" value="${clip.end}"></label></div>
          <label>Audio<select id="tlAudio">${options([['original','Suara asli video'],['voice','Ganti dengan narasi'],['mix','Campur suara & narasi']],clip.audio_mode)}</select></label>
          <label>Naskah narasi<textarea id="tlNarration" rows="3" placeholder="Tulis kalimat untuk sulih suara…"></textarea></label><button class="ghost" data-tl-clip="tts">Buat suara dari teks</button>
        </section>
        <section class="inspector-section" ${this.inspectorTab !== 'subtitles' ? 'hidden' : ''}>
          <h3>Gaya subtitle</h3><button class="ghost" data-creator="words">Editor per kata & terjemahan</button><p class="field-help">${this.presets.length} gaya untuk semua subtitle. Perubahan diperbarui otomatis pada video.</p>
          <button class="caption-generate" data-tl="captions">Buat subtitle otomatis</button>
          <label>Posisi subtitle<select id="tlSubtitlePosition">${options([['bottom','Bawah'],['middle','Tengah'],['top','Atas'],['off','Tanpa subtitle tambahan']],clip.subtitle_position || 'bottom')}</select></label>
          <p class="field-help">Subtitle yang sudah menyatu dengan gambar sumber tidak bisa dihapus. Pilih tanpa subtitle tambahan atau pindahkan posisi agar tidak bertumpuk.</p>
          ${this.presetGallery(clip.subtitle_preset, 'data-preset')}<button class="ghost" data-tl="custom">＋ Buat template sendiri</button>
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
      host.querySelector('#tlHook')?.addEventListener('input', e => { this.clip.title = e.target.value; });
      host.querySelector('[data-creator="words"]')?.addEventListener('click', () => CreatorEditor.words(this));
      host.querySelector('[data-creator="crop"]')?.addEventListener('click', () => CreatorEditor.crop(this));
      host.querySelector('#tlSubtitlePosition')?.addEventListener('change',event=>{this.clip.subtitle_position=event.target.value;});
      host.querySelector('[data-tl="split"]')?.addEventListener('click',async()=>{
        try {
          const at = this.clip.start + ((this.el.querySelector('video')?.currentTime - Number(this.el.querySelector('video')?.dataset.sourceStart || 0)) || (this.clip.end - this.clip.start) / 2);
          await this.save();
          await api(`/api/projects/${state.project.id}/clips/${this.clip.index}/split?at=${at}`,{method:'POST'});
          this.close();state.project=await api(`/api/projects/${state.project.id}`);renderProjectDetail();toast('Klip dipisah. Setiap bagian bisa memiliki ukuran sendiri.');
        } catch(error){toast(error.message,'error');}
      });
      host.querySelector('[data-tl="custom"]')?.addEventListener('click',async()=>{
        const result=await createTypography(); if(!result)return;
        this.presets=await api('/api/subtitle-presets');this.clip.subtitle_preset=result.id;this.templateCategory='Custom';this.renderInspector();
      });
      host.querySelectorAll('[data-inspector]').forEach(node => node.addEventListener('click', () => { this.inspectorTab = node.dataset.inspector; this.renderInspector(); }));
      host.querySelectorAll('[data-category]').forEach(node => node.addEventListener('click', () => { this.templateCategory = node.dataset.category; this.renderInspector(); }));
      host.querySelectorAll('[data-position]').forEach(node => node.addEventListener('click', () => { if (selected) { [selected.x, selected.y] = node.dataset.position.split(',').map(Number); this.renderInspector(); } }));
      host.querySelector('[data-tl="captions"]').addEventListener("click", () => this.generateCaptions());

      const clipStart = host.querySelector("#tlClipStart");
      const clipEnd = host.querySelector("#tlClipEnd");
      const updateTrim = () => {
        const oldStart = this.clip.start;
        this.clip.start = Math.max(0, Number(clipStart.value) || 0);
        this.clip.end = Math.min(state.project.duration, Math.max(this.clip.start + 0.2, Number(clipEnd.value) || 0));
        this.clip.start = Math.min(this.clip.start, this.clip.end - .2);
        const delta = this.clip.start - oldStart, duration = this.clip.end - this.clip.start;
        const shift = rows => (rows || []).filter(c => c.end > delta && c.start < delta + duration).map(c => ({...c,start:Math.max(0,c.start-delta),end:Math.min(duration,c.end-delta),...(c.words ? {words:shift(c.words)} : {})}));
        this.clip.captions = shift(this.clip.captions);
        this.clip.caption_variants=Object.fromEntries(Object.entries(this.clip.caption_variants||{}).map(([lang,rows])=>[lang,shift(rows)]));
        const text = host.querySelector('#tlCaptions'); if (text) text.value = captionsToText(this.clip.captions);
        const base = this.items("video")[0];
        if (base) { base.framing = CreatorEditor.shiftFraming(base.framing,delta,duration); base.srcStart = this.clip.start; base.start = 0; base.end = this.clip.end - this.clip.start; }
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
        this.clip.captions = textToCaptions(captions.value).map((row, i) => {
          const old = this.clip.captions[i];
          return old && old.text === row.text && old.start === row.start && old.end === row.end ? old : row;
        });
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
      const button = this.el.querySelector('[data-tl="captions"]');
      if (button) { button.disabled = true; button.textContent = 'Mentranskrip audio klip…'; }
      try {
        await this.save(true);
        toast("Membuat subtitle dari audio klip dengan model lokal…");
        const job = await api(`/api/projects/${state.project.id}/clips/${this.clip.index}/captions`, { method: "POST" });
        const result = await waitJob(job.id);
        const project = await api(`/api/projects/${state.project.id}`);
        state.project = project;
        const fresh = project.clips.find(c => c.index === this.clip.index);
        if (fresh) this.clip = fresh;
        this.clip.captions = result.captions || this.clip.captions || [];
        this.clip.subtitle_position = "bottom";
        // The ASR job stores captions, but the new subtitle position must also
        // survive an immediate editor close before preview's delayed save runs.
        await this.save(true);
        this.renderInspector();
        if (this.clip.captions.length) {
          this.schedulePreview();
          toast(`${this.clip.captions.length} baris subtitle siap. Pratinjau diperbarui otomatis.`);
        } else {
          toast("Tidak ada ucapan terdeteksi dalam klip ini.", "error");
        }
      } catch (error) { toast(error.message, "error"); }
      finally { this.busy = false; const current = this.el.querySelector('[data-tl="captions"]'); if (current) { current.disabled = false; current.textContent = 'Buat subtitle otomatis'; } }
    },

    /** Simpan timeline + field turunan (crop/kanvas/trim) ke proyek. */
    async save(silent = false) {
      const videoItem = this.items("video")[0];
      const payload = {
        timeline: this.timeline,
        subtitle_preset: this.clip.subtitle_preset,
        subtitle_position: this.clip.subtitle_position,
        audio_mode: this.clip.audio_mode,
        captions: this.clip.captions,
        caption_variants: this.clip.caption_variants || {},
        caption_language: this.clip.caption_language || '',
        title: this.clip.title,
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
      if (!silent) {
        state.project = await api(`/api/projects/${state.project.id}`);
        toast(t("toast.saved"));
        renderProjectDetail();
      }
    },

    async preview() {
      if (!this.el || this.el.hidden) return;
      if (this.busy || this.previewBusy) { this.schedulePreview(); return; }
      this.previewBusy = true;
      const generation = this.generation, fingerprint = this.fingerprint();
      const status = () => this.el.querySelector('#tlPreviewStatus');
      if (status()) status().textContent = 'Memperbarui video…';
      try {
        await this.save(true);
        const job = await api(`/api/projects/${state.project.id}/clips/${this.clip.index}/preview`, { method: "POST" });
        const result = await waitJob(job.id);
        if (generation !== this.generation || this.el.hidden) return;
        if (fingerprint !== this.fingerprint()) { this.schedulePreview(); return; }
        if (result?.mp4) {
          const player = this.el.querySelector('video');
          const position = Math.max(0, (player?.currentTime || 0) - Number(player?.dataset.sourceStart || 0));
          const playing = player && !player.paused;
          this.previewPath = result.mp4;
          this.renderStage(Math.min(position, this.clip.end - this.clip.start - .05), playing);
        }
      } catch (error) {
        if (generation === this.generation && !this.el.hidden && status()) status().textContent = 'Perubahan belum tampil: ' + error.message;
      } finally {
        this.previewBusy = false;
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
      input.onchange = () => resolve(input.files[0] || null);
      input.oncancel = () => resolve(null);
      input.click();
    });
  }

  return {
    open: (index) => editor.open(index),
    close: () => editor.close(),
  };
})();
