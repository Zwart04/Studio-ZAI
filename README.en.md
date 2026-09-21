# 🎬 Studio ZAI

**Cross-platform app that turns long videos into short clips automatically — 100% local, runs on your own machine.**

Studio ZAI takes videos from **YouTube / TikTok / Instagram / local files**, finds the best moments automatically, cuts them into 9:16 clips, adds **automatic subtitles (Indonesian & English)**, and can generate **voiceovers** — including **cloning your own voice**.

Available for **Windows, Linux, and Android**.

> 🇮🇩 Versi Bahasa Indonesia: [README.md](README.md)

---

## ✨ Highlights

| Feature | Description |
|---|---|
| 🔗 **Flexible input** | YouTube, TikTok, Instagram links or local video files |
| ✂️ **Smart auto-clip** | Best-moment detection without AI (loudness + silence + scene) or transcript-based |
| 💬 **Auto subtitles** | Word-level burned-in captions, SRT/VTT export. Indonesian & English |
| 📱 **9:16 vertical crop** | Center & blur-background modes for TikTok/Reels/Shorts |
| 🎙️ **Auto voiceover** | Indonesian & English TTS (Piper — ultra light, realtime on CPU) |
| 🧬 **Voice cloning** | Clone a voice from a 10-30 s sample (Chatterbox 0.5B — Indonesian & English) |
| 🎛️ **Simple editor** | Trim, split, reorder, edit subtitle text, volume, export |
| 🤖 **Model Manager** | Auto-detects hardware → recommends & downloads the right models |
| 🔌 **Offline-first** | Once models are downloaded, everything runs without internet |
| 🌗 **Minimal UI** | Clean dark theme, Indonesian + English |

## 🪶 Why So Light?

- Works even with zero AI — pure ffmpeg heuristic mode for clipping.
- Only the smallest efficient models: **small Whisper** (75-250 MB), **Piper TTS** (~60 MB/voice), never giant models.
- Models are **not bundled** in the installer/APK — downloaded on demand.
- No heavy UI framework (vanilla HTML/CSS/JS on desktop).

## 🚀 Quick Start

### Desktop (Windows / Linux)

```bash
git clone https://github.com/Zwart04/Studio-ZAI.git
cd Studio-ZAI/core
pip install -e .[dev]
studiozai doctor          # detect ffmpeg, GPU, recommended models
studiozai serve           # open http://127.0.0.1:8737
```

### Android

```bash
cd android/app
flutter pub get
flutter build apk --release --split-per-abi
```

Full guide: [docs/BUILD.md](docs/BUILD.md)

## 📖 Documentation

All docs live in [docs/](docs/): [PRD](docs/PRD.md) · [PLAN](docs/PLAN.md) · [FEATURES](docs/FEATURES.md) · [ARCHITECTURE](docs/ARCHITECTURE.md) · [TECH_STACK](docs/TECH_STACK.md) · [MODELS](docs/MODELS.md) · [DESIGN](docs/DESIGN.md) · [BUILD](docs/BUILD.md) · [SECURITY](docs/SECURITY.md) · [CONTRIBUTING](docs/CONTRIBUTING.md) · [CHANGELOG](docs/CHANGELOG.md)

## 📁 Repo Layout

```
Studio ZAI/
├─ core/       # Python engine (desktop): pipeline, CLI, server, model manager
├─ ui/         # Static web UI (used by the desktop app)
├─ desktop/    # pywebview launcher + packaging (PyInstaller/AppImage)
├─ android/    # Flutter app (full on-device)
├─ scripts/    # Dev & deploy scripts
└─ docs/       # Documentation
```

## ⚖️ License & Attribution

Studio ZAI code: **MIT** — see [LICENSE](LICENSE).
Third-party models: Piper (MIT), Whisper (MIT), Chatterbox (MIT), Chatterbox-TTS-Indonesian (Apache-2.0), ZipVoice (Apache-2.0). Details: [docs/MODELS.md](docs/MODELS.md).

> ⚠️ Voice cloning is only for your own voice or voices you have explicit permission to use. All Chatterbox outputs carry an automatic PerTh watermark (model default, MIT).
