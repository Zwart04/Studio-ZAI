import urllib.error
from pathlib import Path

import pytest

from studiozai import projects
from studiozai.pipeline import download


def test_audio_native_fallback_preserves_language_and_cookie_binding(monkeypatch, tmp_path):
    monkeypatch.setattr(download, '_extract', lambda *a: {'title': 'Fixture', 'duration': 30})
    monkeypatch.setattr(download, '_pick_audio_format', lambda *a: {'url': 'https://cdn.invalid/expired', 'ext': 'm4a'})
    def failed(url, path, *a):
        path.write_bytes(b'partial')
        raise RuntimeError('HTTP 403')
    monkeypatch.setattr(download, '_http_download', failed)
    called = []
    def native(url, directory, cookies, progress, language):
        called.append((cookies, language))
        assert not (directory / 'Fixture.m4a').exists()
        path = directory / 'recovered.m4a'
        path.write_bytes(b'audio')
        return path, {'title': 'Fixture', 'duration': 30}
    monkeypatch.setattr(download, '_download_audio_native', native)
    result = download.download_audio('https://youtu.be/oPZY7nKtUTc', tmp_path, cookies='private-cookie-file', audio_lang='id')
    assert called == [('private-cookie-file', 'id')]
    assert Path(result['path']).read_bytes() == b'audio'


def test_audio_http_error_retains_status_without_url(monkeypatch, tmp_path):
    def failed(*a):
        raise urllib.error.HTTPError('https://cdn.invalid/signed-private-query', 403, 'Forbidden', {}, None)
    monkeypatch.setattr(download, '_http_open', failed)
    with (tmp_path / 'audio').open('wb') as handle, pytest.raises(RuntimeError, match='HTTP 403') as error:
        download._http_copy('https://cdn.invalid', handle)
    assert 'signed-private-query' not in str(error.value)


@pytest.mark.parametrize('url', ['https://youtu.be/oPZY7nKtUTc', 'https://www.youtube.com/watch?v=oPZY7nKtUTc', 'https://youtube.com/shorts/oPZY7nKtUTc'])
def test_source_thumbnail_is_available_before_render(url):
    assert projects.source_thumbnail_url(url) == 'https://i.ytimg.com/vi/oPZY7nKtUTc/hqdefault.jpg'


def test_thumbnail_does_not_accept_other_hosts_or_invalid_ids():
    assert projects.source_thumbnail_url('https://youtube.com.attacker.invalid/watch?v=oPZY7nKtUTc') == ''
    assert projects.source_thumbnail_url('https://youtu.be/not-valid') == ''
