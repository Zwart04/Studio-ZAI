# Studio ZAI 1.5.1 — validation report

Validated on Windows, 22 September 2026. APKs were compiled on this host; no physical Android device was connected.

## Changes

- Selected YouTube audio language is honored together with video quality on desktop. Android downloads the selected audio stream separately and merges it with video.
- Original and square canvases keep their aspect ratio in export and preview. Framing no longer assumes every output is 9:16.
- Editor changes are saved into the render timeline. Automatic captions can be generated from the editor; typography applies to all clip captions. Original-audio mode ignores a previous voiceover track.
- 24 text templates across Essential, Pop, Neon, Editorial, and Label, with bundled OFL fonts. Nine-point positioning and percentage coordinates replace text-position sliders.
- Responsive project cards, labeled source choices, field explanations, and a synchronized recent-project list after deletion. Application colors follow the existing Apple-style design tokens.
- Closing a preview pauses playback and releases its source. Late preview results do not restart hidden players.
- Required first-run setup validates installation. Desktop Whisper weights are downloaded during setup rather than leaving an installation marker alone. Android downloads/extracts model archives with bounded buffering, background extraction, and retryable errors.
- Android ASR and highlight analysis stream PCM audio in bounded chunks and run heavy work outside the UI isolate. Adaptive launcher icons have safe insets; the in-app logo retains its original contrast.
- The desktop model registry and manager are included in source control; a broad `models/` ignore rule previously excluded this source package.

## Automated and packaged checks

| Check | Result |
| :-- | :-- |
| Python engine suite | 97 passed; two existing FastAPI lifecycle deprecation warnings |
| Ruff | Passed |
| JavaScript syntax | Passed for app and timeline |
| Flutter analysis | No issues |
| Flutter tests | 8 passed |
| Android long WAV regression | 65-minute PCM file, at most 16,000 samples per reader chunk |
| Android model download tests | Local HTTP download, background extraction, corrupt/traversal archives rejected |
| Font catalog parity | All 24 style IDs and colors match; bundled creator fonts are identical on both platforms |
| Windows package | EXE server starts, v1.5.1 health endpoint, 24 presets, bundled CSS/fonts, source ingest, clip processing, subtitle preview render |
| Android artifacts | ARM64, ARMv7, and x86_64 release APKs built; ARM64 signing certificate matches v1.5.0 |
| Browser checks | Source controls, captions, typography, positioning, previews, playback cleanup, responsive 390px layout |

## Real long-video test

User-selected source: [I Ate Breakfast From Every Country](https://youtu.be/kIB-ypmiIzo), duration reported by YouTube: **4,686 seconds / 78:06**.

The complete video was downloaded at 480p with the **Indonesian** audio track. The local file reports 4,685.454 seconds. Whisper Tiny processed the entire file in eight chunks and produced **1,874 segments**, with the final segment ending at **4,680.5 seconds**. The recognized speech was Indonesian; Tiny still makes spelling errors, so captions should be reviewed.

The automatic selector returned three clips. Additional 12-second windows checked boundaries across the source:

| Source start | Canvas | Template | Export | Caption rows | Preview |
| :-- | :-- | :-- | :-- | :-- | :-- |
| 00:30 | Original | Viral Yellow | 854 × 480 | 10 | Aspect ratio and audio passed |
| 01:00:50 | Square | Editorial | 1080 × 1080 | 9 | Aspect ratio and audio passed |
| 01:17:40.454 | Portrait | Pink Label | 1080 × 1920 | 8 | Aspect ratio and audio passed |

All exports contain video and audio and are approximately 12 seconds long. Extra timeline text was positioned at 50% X / 18% Y during these renders.

The Android YouTube library was also exercised against this URL on the build host. Its manifest exposed `id.3`, four Indonesian audio streams, and 22 video streams. This verifies track discovery and matching; it does not replace playback and native-model testing on a phone.

Reproduce the opt-in network test with an installed Whisper Tiny model:

```bash
python tools/verify_long_video.py https://youtu.be/kIB-ypmiIzo
```

Downloads, transcripts, clips, and the machine-readable report stay under ignored `build/long-video-qa/`. The source video and its clips are not distributed in the repository or release. README media uses an original synthetic demo.

## Known scope limits

- Physical-device Android installation, model inference, and long-video playback still need device verification.
- Standard Windows binaries do not bundle PyTorch/Chatterbox. Desktop cloning requires the documented optional source runtime; local LLM ranking requires a separately configured server.
- Source-site access and caption accuracy depend on external services, language, model, and recording quality.

## Release assets

Windows x64 ZIP, three architecture-specific APKs, an MP4 UI demo, and `SHA256SUMS.txt`. Extract the full Windows archive. Complete the new setup flow when upgrading from earlier versions.
