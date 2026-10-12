"""Copy installed dependency notices; never read application data or model weights."""
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
PACKAGES=('ctranslate2','faster-whisper','piper-tts','sherpa-onnx','onnxruntime','tokenizers','yt-dlp','yt-dlp-ejs','opencv-python','opencv-python-headless')


def main():
    target=ROOT/'docs/licenses/runtime'
    count=0
    for name in PACKAGES:
        try:
            package=distribution(name)
        except PackageNotFoundError:
            continue
        for relative in package.files or []:
            if 'license' not in str(relative).lower() and Path(relative).name != 'COPYING':
                continue
            source=Path(package.locate_file(relative))
            if source.is_file() and source.stat().st_size < 1024*1024:
                output=target/f'{name}-{package.version}-{source.name}'
                output.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(source,output)
                count+=1
    print('Dependency notices copied:',count)


if __name__=='__main__':
    main()
