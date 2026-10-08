import json
import zipfile

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from studiozai import ai, config, credentials, server
from studiozai.pipeline.framing import select_face


@pytest.fixture
def isolated(monkeypatch, tmp_path):
    monkeypatch.setattr(config, '_base_dir', lambda: tmp_path)
    ai._MODEL_CACHE.clear()
    return tmp_path


def test_discovery_uses_account_catalog_filters_tasks_and_does_not_echo_key(isolated, monkeypatch):
    calls = []
    def listing(base, route, key, **kwargs):
        calls.append((base, route, key))
        return {'data': [{'id': 'gpt-5-mini'}, {'id': 'gpt-5'}, {'id': 'text-embedding-3'}, {'id': 'gpt-image-1'}, {'id': 'inactive-mini', 'active': False}]}
    monkeypatch.setattr(ai, 'request', listing)
    result = ai.discover_models('openai', key='fixture-only')
    assert result['recommended'] == 'gpt-5-mini'
    assert {m['id'] for m in result['models']} == {'gpt-5', 'gpt-5-mini'}
    assert 'fixture-only' not in json.dumps(result)
    assert ai.discover_models('openai', key='fixture-only') == result
    assert len(calls) == 1
    ai.discover_models('openai', key='different-fixture')
    assert len(calls) == 2
    assert not (isolated / 'settings.json').exists()


@pytest.mark.parametrize('response', [{'data': []}, [], {'data': 'invalid'}])
def test_missing_catalog_never_invents_available_models(isolated, monkeypatch, response):
    monkeypatch.setattr(ai, 'request', lambda *a, **kw: response)
    with pytest.raises(ValueError):
        ai.discover_models('groq', key='fixture')


@pytest.mark.parametrize('base', ['http://api.openai.com/v1', 'https://example.com/v1', 'https://api.openai.com:8443/v1', 'https://api.openai.com/v1?key=private'])
def test_official_provider_cannot_send_credentials_to_changed_host(base):
    with pytest.raises(ValueError):
        ai.validate_provider_base('openai', base)


def test_changing_custom_endpoint_removes_old_key(isolated):
    config.save_settings({'ai_provider': 'compatible', 'ai_base_url': 'https://first.example/v1', 'ai_api_key': 'fixture'})
    config.save_settings({'ai_base_url': 'https://second.example/v1', 'ai_api_key': '***'})
    assert not credentials.read()['ai_api_key']


def test_model_discovery_rejects_reuse_of_saved_key_on_another_endpoint(isolated, monkeypatch):
    config.save_settings({'ai_provider': 'compatible', 'ai_base_url': 'https://first.example/v1', 'ai_api_key': 'fixture'})
    monkeypatch.setattr(ai, 'discover_models', lambda *a: pytest.fail('Key must not reach network'))
    with pytest.raises(HTTPException) as exc:
        server.online_models(server.ModelDiscovery(provider='compatible', base_url='https://second.example/v1', use_saved_key=True))
    assert exc.value.status_code == 400


def test_private_files_and_cross_site_requests_are_blocked(isolated):
    with TestClient(server.app) as client:
        for name in ['credentials.json', 'settings.json', '.env', 'private.sqlite', 'export-private.json']:
            target = isolated / name
            target.write_text('fixture-only')
            assert client.get('/api/media', params={'path': str(target)}).status_code == 403
        media = isolated / 'video.mp4'
        media.write_bytes(b'fixture')
        assert client.get('/api/media', params={'path': str(media)}).status_code == 200
        assert client.get('/api/health', headers={'origin': 'https://evil.example'}).status_code == 403
        assert client.get('/api/health', headers={'host': 'evil.example'}).status_code == 403
        assert client.post('/api/ai/models', json={'provider': 'openai', 'api_key': 'fixture'}, headers={'sec-fetch-site': 'cross-site'}).status_code == 403
        assert client.get('/api/health', headers={'origin': 'http://testserver'}).status_code == 200


def test_face_choice_holds_position_when_selected_face_disappears():
    assert select_face([(.22, .4), (.8, .4)], (.2, .4)) == (.22, .4)
    assert select_face([(.8, .4)], (.2, .4)) is None
    assert select_face([], (.2, .4)) is None


def test_zip_contains_only_selected_rendered_videos(isolated, monkeypatch):
    from studiozai import projects
    project = projects.Project.create('fixture')
    video = project.root / 'clip.mp4'
    video.write_bytes(b'fixture-video')
    clip = projects.Clip(index=0, start=0, end=1, title='Test')
    clip.files['mp4_portrait'] = str(video)
    project.set_clips([clip])
    project.save()
    class Job:
        def check_cancel(self): pass
        def report(self, *args): pass
    class Submission:
        def __init__(self, result): self.result = result
        def as_dict(self): return self.result
    monkeypatch.setattr(server.jobs.MANAGER, 'submit', lambda kind, title, fn: Submission(fn(Job())))
    result = server.clips_zip(project.id, server.BatchRenderRequest(clips=[0], formats=['portrait']))
    with zipfile.ZipFile(result['zip']) as bundle:
        assert len(bundle.namelist()) == 1
        assert bundle.read(bundle.namelist()[0]) == b'fixture-video'
    assert result['count'] == 1
