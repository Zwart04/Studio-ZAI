import base64
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from studiozai import ai, config, credentials, server


@pytest.fixture
def local_ai(monkeypatch, tmp_path):
    monkeypatch.setattr(config, '_base_dir', lambda: tmp_path)
    captured = []
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            captured.append((self.path, dict(self.headers), body))
            if self.path.endswith('/messages'):
                response = json.dumps({'content':[{'type':'text','text':'Anthropic response'}]}).encode()
            elif self.path.endswith('/images/generations'):
                response = json.dumps({'data':[{'b64_json':base64.b64encode(b'\x89PNG\r\n\x1a\nfixture').decode()}]}).encode()
            elif self.path.endswith('/audio/speech'):
                response = b'RIFFfixture WAVE'
            else:
                response = json.dumps({'choices':[{'message':{'content':'AI response'}}]}).encode()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(response)
        def log_message(self, *_):
            pass
    host = HTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=host.serve_forever, daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{host.server_port}/v1', captured
    host.shutdown()
    host.server_close()
    thread.join()


def test_keys_are_protected_redacted_preserved_and_removed(monkeypatch, tmp_path):
    monkeypatch.setattr(config, '_base_dir', lambda: tmp_path)
    config.save_settings({'ai_provider':'openai','ai_api_key':'test-private-key'})
    assert credentials.read()['ai_api_key'] == 'test-private-key'
    assert 'test-private-key' not in config.settings_path().read_text()
    assert 'test-private-key' not in (tmp_path/'credentials.json').read_text()
    assert server.get_settings()['ai_api_key'] == '***'
    config.save_settings({'ai_api_key':'***'})
    assert credentials.read()['ai_api_key'] == 'test-private-key'
    config.save_settings({'ai_provider':'deepseek','ai_api_key':'***'})
    assert not credentials.read()['ai_api_key']


@pytest.mark.parametrize('provider,route,answer',[('compatible','/v1/chat/completions','AI response'),('anthropic','/v1/messages','Anthropic response'),('deepseek','/v1/chat/completions','AI response')])
def test_text_provider_protocols(local_ai, provider, route, answer):
    base, captured = local_ai
    config.save_settings({'ai_provider':provider,'ai_base_url':base,'ai_model':'fixture-model','ai_api_key':'fixture-key'})
    assert ai.text('Select a clip') == answer
    path, headers, body = captured[0]
    assert path == route and body['model'] == 'fixture-model'
    assert body['messages'][0]['content'] == 'Select a clip'
    if provider == 'anthropic':
        assert headers['X-Api-Key'] == 'fixture-key' and body['max_tokens'] > 0
    else:
        assert headers['Authorization'] == 'Bearer fixture-key'


def test_image_and_voice_outputs_are_stored_locally(local_ai):
    base, captured = local_ai
    config.save_settings({'image_provider':'sd_local','image_base_url':base,
                          'speech_provider':'openai','speech_base_url':base,'speech_api_key':'fixture-key'})
    picture = ai.image('A quiet studio')
    assert picture.is_file() and picture.with_suffix('.json').is_file()
    assert captured[-1][2]['size'] == '512x512'
    sound = ai.speech('Selamat pagi', 'marin', 'id')
    assert sound.read_bytes().startswith(b'RIFF')
    assert captured[-1][2]['instructions'] == 'Speak in Indonesian.'
    with pytest.raises(ValueError):
        ai.speech('Hello', 'unknown', 'en')


def test_keys_cannot_travel_over_plain_remote_http():
    with pytest.raises(ValueError, match='HTTPS'):
        ai.request('http://example.com', '/test', 'private', {})
