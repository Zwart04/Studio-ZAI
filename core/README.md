# Studio ZAI — Core Engine (Python)

Mesin desktop Studio ZAI: pipeline unduh → transkrip → auto-clip → subtitle → crop → suara → render, plus Manajer Model dan server UI lokal.

**English:** Python engine behind the Studio ZAI desktop app. Install with `pip install -e ".[dev]"`, check your machine with `studiozai doctor`, then run the app with `studiozai serve`. Push pipeline: yt-dlp → faster-whisper → heuristic/optional-LLM highlight → ffmpeg render → Piper/Chatterbox voice. The small YuNet face detector is bundled; larger speech/image models are not bundled and they are fetched on demand through the Model Manager.

Dokumentasi lengkap ada di [../docs](../docs) — mulai dari [../docs/BUILD.md](../docs/BUILD.md).
