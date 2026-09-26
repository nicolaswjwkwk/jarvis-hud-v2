#!/usr/bin/env python3
"""Dependency-free mobile server and local/OpenAI-compatible model gateway."""
from __future__ import annotations
import json, os, pathlib, urllib.error, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
ROOT = pathlib.Path(__file__).resolve().parent.parent
HOST = os.getenv('JARVIS_HOST', '127.0.0.1')
PORT = int(os.getenv('JARVIS_PORT', '8080'))
MODEL_URL = os.getenv('JARVIS_MODEL_URL', 'http://127.0.0.1:11434/v1/chat/completions')
DEFAULT_MODEL = os.getenv('JARVIS_MODEL', 'llama3.2')
MAX_BODY = 2 * 1024 * 1024

class Handler(BaseHTTPRequestHandler):
    server_version = 'JARVIS-Mobile/1.1'
    def log_message(self, fmt: str, *args: Any) -> None:
        print(f'[{self.log_date_time_string()}] {fmt % args}')
    def send_json(self, status: int, payload: Any) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data))); self.send_header('Cache-Control','no-store')
        self.send_header('Access-Control-Allow-Origin','*'); self.end_headers(); self.wfile.write(data)
    def do_OPTIONS(self) -> None:
        self.send_response(204); self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Headers','Content-Type, Authorization')
        self.send_header('Access-Control-Allow-Methods','GET, POST, OPTIONS'); self.end_headers()
    def do_GET(self) -> None:
        path = self.path.split('?', 1)[0]
        if path == '/health': return self.send_json(200, {'ok':True,'service':'jarvis-mobile','model_url':MODEL_URL})
        if path == '/api/config': return self.send_json(200, {'ok':True,'endpoint':'/v1/chat/completions','model':DEFAULT_MODEL})
        if path == '/api/models':
            try: return self.send_json(200, json.loads((ROOT/'models/free-models.json').read_text(encoding='utf-8')))
            except OSError as exc: return self.send_json(500, {'error':str(exc)})
        self.serve_static()
    def do_POST(self) -> None:
        if self.path not in ('/v1/chat/completions','/api/chat'): return self.send_json(404, {'error':'endpoint_not_found'})
        try:
            length = int(self.headers.get('Content-Length','0'))
            if not 0 < length <= MAX_BODY: raise ValueError('request body must be between 1 byte and 2 MiB')
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict) or not isinstance(payload.get('messages'), list): raise ValueError('messages must be an array')
            payload.setdefault('model', DEFAULT_MODEL); payload['stream'] = False
            request = urllib.request.Request(MODEL_URL, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type':'application/json'}, method='POST')
            with urllib.request.urlopen(request, timeout=120) as response: body, status = response.read(MAX_BODY), response.status
            self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(body))); self.send_header('Access-Control-Allow-Origin','*'); self.end_headers(); self.wfile.write(body)
        except (ValueError, json.JSONDecodeError) as exc: self.send_json(400, {'error':{'message':str(exc),'type':'invalid_request'}})
        except (urllib.error.URLError, TimeoutError) as exc: self.send_json(502, {'error':{'message':f'local model unavailable: {exc}','type':'upstream_error'}})
        except Exception as exc: self.send_json(500, {'error':{'message':str(exc),'type':'server_error'}})
    def serve_static(self) -> None:
        requested = self.path.split('?',1)[0].lstrip('/') or 'jarvis-x.html'; candidate = (ROOT/requested).resolve()
        try: candidate.relative_to(ROOT.resolve())
        except ValueError: return self.send_json(403, {'error':'forbidden'})
        if candidate.is_dir(): candidate /= 'index.html'
        if not candidate.is_file(): return self.send_json(404, {'error':'file_not_found'})
        content_types = {'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.webmanifest':'application/manifest+json','.png':'image/png','.txt':'text/plain','.xml':'application/xml'}
        body = candidate.read_bytes(); self.send_response(200); self.send_header('Content-Type',content_types.get(candidate.suffix,'application/octet-stream')+'; charset=utf-8'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)

if __name__ == '__main__':
    print(f'JARVIS mobile server: http://localhost:{PORT}')
    print(f'Model endpoint: {MODEL_URL} ({DEFAULT_MODEL})')
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
