<p align="center"><img src="assets/logo.png" width="112" alt="Studio ZAI logo" /></p>
<h1 align="center">Studio ZAI</h1>
<p align="center"><strong>Turn long videos into short stories.</strong><br />Automatic clips, captions, a timeline editor, and local voiceovers.</p>
<p align="center"><a href="https://github.com/Zwart04/Studio-ZAI/releases/latest"><strong>Download</strong></a> · <a href="#preview">Preview</a> · <a href="docs/BUILD.md">Build guide</a> · <a href="README.md">Bahasa Indonesia</a></p>

## Preview

![Studio ZAI editor](docs/screenshots/04-editor.png)

Edit video, media, text, and audio tracks in one workspace. Choose a canvas, generate captions, apply a typography template, and check a quick preview before exporting.

![Recorded editor preview](docs/screenshots/studio-zai-demo.gif)

*Recorded from the desktop UI using original synthetic demo media. Captions can be corrected in the editor. [Download the MP4 demo](https://github.com/Zwart04/Studio-ZAI/releases/download/v1.5.1/StudioZAI-1.5.1-demo.mp4).*

## Download

| Platform | Package |
| :-- | :-- |
| Windows 10/11 x64 | [Windows ZIP](https://github.com/Zwart04/Studio-ZAI/releases/download/v1.5.1/StudioZAI-1.5.1-windows-x64.zip) |
| Android 8+ ARM64 | [ARM64 APK](https://github.com/Zwart04/Studio-ZAI/releases/download/v1.5.1/StudioZAI-1.5.1-android-arm64.apk) |
| Android ARMv7 | [32-bit ARM APK](https://github.com/Zwart04/Studio-ZAI/releases/download/v1.5.1/StudioZAI-1.5.1-android-armv7.apk) |
| Android x86_64 | [x86_64 APK](https://github.com/Zwart04/Studio-ZAI/releases/download/v1.5.1/StudioZAI-1.5.1-android-x86_64.apk) |

Extract the entire Windows ZIP before opening `StudioZAI.exe`; FFmpeg is included. AI models are downloaded during first-run setup. Network access is needed for model downloads and online sources; local media processing works offline once models are installed. Linux can be built from source.

[Release notes](https://github.com/Zwart04/Studio-ZAI/releases/tag/v1.5.1) · [SHA-256 checksums](https://github.com/Zwart04/Studio-ZAI/releases/download/v1.5.1/SHA256SUMS.txt)

## Start in three steps

1. **Complete setup.** Install transcription and speech models. Android also prepares voice activity detection and offers optional English cloning. Failed downloads remain retryable.
2. **Add a video.** Select a local file or supported link, then choose the transcript language, clip count, and original, portrait, square, or landscape canvas.
3. **Edit and export.** Generate captions, correct the wording, choose a style, and adjust your tracks. Use **Quick preview** before exporting the final video.

> A transcript is recognized speech. Captions place that text at specific times in a video. Selecting a transcript language does not translate or replace the original audio. Choose the available Indonesian audio track to download an Indonesian YouTube dub.

## Features

| Feature | What it does |
| :-- | :-- |
| Automatic clips | Finds moments using audio energy, speech density, and pauses. |
| Timeline editor | Video, image/video overlays, text, and extra audio tracks. |
| Automatic captions | Local Whisper transcription, editable timing/text, and captions burned into MP4. |
| 24 typography templates | Essential, Pop, Neon, Editorial, and Label styles with bundled fonts and distinct colors. |
| Canvas and position | Original aspect ratio, 9:16, 1:1, 16:9; fit, crop, blur; 3 × 3 position presets and precise percentages. |
| Local voiceover | Indonesian and English Piper voices. |
| Multilingual audio | Select available YouTube tracks without silently falling back to another language. |
| Guided setup | Model downloads, installation validation, and retryable errors. |

## Screenshots

| Home | Models |
| :--: | :--: |
| ![Home](docs/screenshots/01-home.png) | ![Models](docs/screenshots/02-models.png) |

| Voiceover | Setup |
| :--: | :--: |
| ![Voiceover](docs/screenshots/03-voice.png) | ![Setup](docs/screenshots/06-setup.png) |

These are desktop UI screenshots. The [small-screen web screenshot](docs/screenshots/05-mobile-home.png) demonstrates responsive layout and is not an APK screenshot.

## Validation and limitations

Version 1.5.1 was tested with a **78-minute YouTube video** containing an Indonesian audio track: a complete 480p download, 1,874 transcript segments, three automatically selected clips, and renders/previews near the start, after minute 60, and near the end. Original, square, and portrait aspect ratios were checked with FFprobe. See the [validation report](docs/RELEASE-1.5.1.md).

- Desktop uses yt-dlp for supported websites. Android supports YouTube, direct media URLs, and local files. Source-site access may change or require authentication.
- Android cloning uses ZipVoice for English. Desktop cloning requires a source installation with the additional Chatterbox runtime; the Windows package does not bundle PyTorch/Chatterbox.
- Desktop LLM ranking is optional and requires a separately configured compatible server, such as Ollama.
- Caption accuracy depends on the language, model, and recording. Review text before publishing.
- Android validation covers builds, Flutter analysis, and automated tests. A physical Android device was not available for this release.

## Development

```bash
git clone https://github.com/Zwart04/Studio-ZAI.git
cd Studio-ZAI
python -m venv .venv
# Activate the environment, then:
pip install -e "core[media,asr,tts,desktop,dev]"
studiozai serve
python -m pytest core/tests
```

```bash
cd android/app
flutter pub get
flutter analyze
flutter test
flutter build apk --release --split-per-abi
```

[Architecture](docs/ARCHITECTURE.md) · [Build and signing](docs/BUILD.md) · [Models and licenses](docs/MODELS.md) · [Design system](docs/DESIGN.md)

## License and credits

Studio ZAI code is [MIT licensed](LICENSE). Models and dependencies retain their own licenses. Anton, Barlow Condensed, DM Serif Display, and Kalam are bundled with their OFL notices. The application follows its existing Apple-style neutral palette and system-blue accent; colorful typography is confined to video templates.

Built with FFmpeg, yt-dlp, faster-whisper, Piper, Flutter, and sherpa-onnx. Workflow inspiration: [openshorts](https://github.com/mutonby/openshorts) and [OpenCreator](https://github.com/krillinai/OpenCreator).
