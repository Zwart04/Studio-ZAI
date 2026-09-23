<p align="center"><img src="assets/brand-banner.svg" width="800" alt="Studio ZAI — Video. Voice. Images." /></p>
<p align="center">A simple creative studio for Windows and Android.<br />Edit video, style captions, create voiceovers, and generate images.</p>
<p align="center"><a href="https://github.com/Zwart04/Studio-ZAI/releases/latest"><strong>Download v1.6.0</strong></a> · <a href="README.md">Bahasa Indonesia</a> · <a href="docs/BUILD.md">Build guide</a></p>

![Studio ZAI editor](docs/screenshots/04-editor.jpg)

## Download

- [Windows x64 ZIP](https://github.com/Zwart04/Studio-ZAI/releases/download/v1.6.0/StudioZAI-1.6.0-windows-x64.zip): extract the entire folder, then run StudioZAI.exe. FFmpeg, speech recognition, Piper, and ZipVoice runtimes are bundled; download models separately.
- [Android universal APK](https://github.com/Zwart04/Studio-ZAI/releases/download/v1.6.0/StudioZAI-1.6.0-android.apk): one package for ARM64, ARMv7, and x86_64, Android 8+.
- [Checksums](https://github.com/Zwart04/Studio-ZAI/releases/download/v1.6.0/SHA256SUMS.txt) · [Release validation](docs/RELEASE-1.6.0.md)

## Create in one place

**Video.** Import a file or supported URL. Select a source audio track, generate clips, trim and split, keep the original aspect ratio, edit captions, and add text, media, or music. Downloaded source video stays in the project for later selections without another download. Save your own typography templates alongside 24 built-in styles.

**Voice.** Choose Indonesian or English Piper voices, use 13 optional OpenAI voices, or record/upload a reference for ZipVoice cloning. ZipVoice supports English/Mandarin and needs the matching reference transcript; Indonesian cloning is not available in the standard package.

**Images.** Enter a prompt and use OpenAI or connect your own stable-diffusion.cpp server. Local image generation requires a separately installed server/model; it is not a native Android image engine. Mobile can use an online provider or your HTTPS server.

**Optional AI.** Configure OpenAI, Anthropic, DeepSeek, or a compatible/Ollama text endpoint to select moments from transcripts. API keys are protected with Windows account encryption / Android secure storage. A ChatGPT app subscription does not provide API credit.

![A short tour of the actual desktop UI](docs/screenshots/studio-zai-demo.gif)

## Getting started

1. Complete setup and download the models you need. Whisper Small is recommended for Indonesian accuracy when hardware permits; Tiny prioritizes speed.
2. Import video. Transcription language does not translate audio: choose an available Indonesian dub track when needed.
3. Edit a clip, choose a caption style, play immediately, and export. Edits refresh the preview automatically. Use **Take a range from source video** to create another clip from the stored source.

Transcripts are speech text; captions place that text in time. Rendered captions are no longer duplicated by an extra player track. Text already burned into the source cannot be removed: disable additional captions or move them.

## Scope and verification

This release includes bounded Android stream retries, long-video progress fixes, independent duplicated projects, safer cache cleanup, reusable source video, custom typography, and optional image/text/speech API integrations. The full 78-minute Indonesian audio source was downloaded using the Android Dart downloader on Windows; multi-chunk transcription was tested beyond minute 60. Python/Flutter tests and package checks are documented in the [release report](docs/RELEASE-1.6.0.md).

Physical Android devices, microphone hardware, and paid cloud providers were not tested live for this release. YouTube restrictions and server changes may still affect downloads. Keep Android open during long jobs. Model speed, memory use, and transcription quality vary by device; no claim is made that image diffusion runs well on every phone.

Screenshots show the desktop web UI with synthetic demo media. The responsive mobile screenshot is not an APK screenshot. No demo MP4 is included in release downloads.

## Development

```bash
pip install -e "core[media,asr,tts,desktop,dev]"
studiozai serve
python -m pytest core/tests
# Android, from android/app:
flutter pub get
flutter analyze
flutter test
flutter build apk --release
```

[Models and licensing](docs/MODELS.md) · [AI setup](docs/AI.md) · [Feature matrix](docs/FEATURES.md) · [Architecture](docs/ARCHITECTURE.md)

Application code: [MIT](LICENSE). Dependencies, voice weights, and fonts retain their own licenses. Workflow references: [openshorts](https://github.com/mutonby/openshorts), [OpenCreator](https://github.com/krillinai/OpenCreator).
