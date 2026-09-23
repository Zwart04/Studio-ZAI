<p align="center"><img src="assets/brand-banner.svg" width="840" alt="Studio ZAI — Video, Voice, Images" /></p>

<p align="center">A simple video studio for Windows and Android. Find moments in long videos, edit them directly, and make captions, voiceovers, and images with local models.</p>

<p align="center"><a href="https://github.com/Zwart04/Studio-ZAI/releases/latest"><strong>Download v1.7.0</strong></a> · <a href="README.md">Bahasa Indonesia</a> · <a href="docs/FEATURES.md">Platform features</a> · <a href="docs/MODELS.md">Models</a></p>

![Studio ZAI editor with a playable video, captions, and timeline](docs/screenshots/04-editor.jpg)

## A studio for video, voice, and images

**Auto-clips and editing.** Import a local file or supported URL, select the actual source audio track, and let the adaptive clip selector find the start of a topic or product review. The source stays with the project so you can choose another range without downloading it again. The editor plays the video inline and supports trim, split, original/9:16/1:1/16:9 canvas, timed captions, text, media, and music. Pick from 24 text styles or save your own.

**Local voice.** Piper voices and ten Supertonic 3 voices read Indonesian and English text. Record from a microphone or import a reference for ZipVoice cloning in English/Mandarin; Indonesian voice cloning is not part of the standard package. Online OpenAI voices are optional.

**Local images.** SDXS-512 generates 512×512 images on Windows and ARM64 Android after a separate 683 MB model download. Prompts stay on device in local mode. Cloud image generation remains optional.

The installed models work without an API key. Downloading a model or a video URL needs internet, while editing imported files and running local models can be offline. Optional OpenAI, Anthropic, DeepSeek, and compatible endpoints support AI tasks where configured.

## Download

| Platform | Package | Notes |
| :-- | :-- | :-- |
| Windows 10/11 x64 | [Windows ZIP](https://github.com/Zwart04/Studio-ZAI/releases/download/v1.7.0/StudioZAI-1.7.0-windows-x64.zip) | Extract the whole folder and run **StudioZAI.exe**. FFmpeg and AI runtimes are bundled; model weights download separately. |
| Android 8+ | [One universal APK](https://github.com/Zwart04/Studio-ZAI/releases/download/v1.7.0/StudioZAI-1.7.0-android.apk) | Local image inference requires ARM64. |

[Release validation](docs/RELEASE-1.7.0.md) · [SHA-256 checksums](https://github.com/Zwart04/Studio-ZAI/releases/download/v1.7.0/SHA256SUMS.txt) · [Build guide](docs/BUILD.md)

## Get started

1. Complete the initial setup and install a speech recognition model. Whisper Base is a good starting point; Small may improve Indonesian accuracy if the device has enough RAM. Add voice and image models only when needed.
2. Paste a link or choose a local video. Put **content language** beside **source audio track**; the transcript language does not translate the audio. Android accepts public YouTube links and direct video URLs. Import a downloaded file for TikTok/Instagram on Android; desktop uses sites supported by yt-dlp.
3. Choose a clip count, generate, and open the project. Play the video immediately in the editor, refine its range and captions, then export. Use **Take a range from source** to create another clip without downloading again.

A **transcript** is speech text used to find moments; **captions** are timed text shown on the video. If the source already contains burned-in text, disable or reposition the extra captions. Supertonic offers ten voice characters for Indonesian/English synthesis; it does not clone a speaker.

## See the app

![A short tour of the Studio ZAI interface](docs/screenshots/studio-zai-demo.gif)

| Home | Voice | Images |
| :--: | :--: | :--: |
| ![Home and clip options](docs/screenshots/01-home.jpg) | ![Voice selection and recording](docs/screenshots/03-voice.jpg) | ![Local image generation](docs/screenshots/07-images.jpg) |

These screenshots show the desktop web UI with documentation media. The [narrow home](docs/screenshots/05-mobile-home.jpg) and [narrow editor](docs/screenshots/09-mobile-editor.jpg) test responsive web layout, not the APK. The GIF is a UI tour; release downloads contain no demo MP4.

The release was tested with a real 80.5-minute speaker review for topic boundaries and audio-preserving export. [The validation report](docs/RELEASE-1.7.0.md) gives the exact coverage and limits. A physical Android device was not available for end-to-end testing in this session. Image generation speed and memory use depend on the device; ARM32 does not have a native local image engine. Private, region-blocked, or login-only video URLs may fail.

## Development

```powershell
git clone https://github.com/Zwart04/Studio-ZAI.git
cd Studio-ZAI
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e "core[media,asr,tts,desktop,dev]"
.venv/Scripts/python.exe -m studiozai serve
.venv/Scripts/python.exe -m pytest core/tests
```

```powershell
cd android/app
flutter pub get
flutter analyze
flutter test
flutter build apk --release
```

[Models and licenses](docs/MODELS.md) · [AI setup](docs/AI.md) · [Features by platform](docs/FEATURES.md) · [Architecture](docs/ARCHITECTURE.md)

Application code: [MIT](LICENSE). Dependencies, fonts, and model weights retain their respective licenses. Workflow references: [openshorts](https://github.com/mutonby/openshorts) and [OpenCreator](https://github.com/krillinai/OpenCreator).
