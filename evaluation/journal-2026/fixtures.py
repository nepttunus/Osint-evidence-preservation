"""Versioned local ground truth for the journal evaluation; synthetic data only."""
import json
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

CASES = ['static', 'delayed-dom', 'fetch', 'redirect', 'console', 'failed-resource', 'iframe', 'dynamic', 'state']
STYLE = 'body{font:24px sans-serif;background:white;margin:24px} #result{background:rgb(17,199,83);padding:20px} iframe{width:700px;height:220px}'

def page(name, body):
    return ('<!doctype html><html><head><meta charset="utf-8"><title>Fixture '+name+'</title>'
            '<link rel="stylesheet" href="/style.css"></head><body>'+body+'</body></html>').encode()

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_GET(self):
        path = urlsplit(self.path).path
        code, mime, headers = 200, 'text/html; charset=utf-8', {}
        if path == '/redirect':
            code, headers, body = 302, {'Location': '/static.html'}, b''
        elif path == '/style.css':
            mime, body = 'text/css', STYLE.encode()
        elif path == '/image.svg':
            mime, body = 'image/svg+xml', b'<svg xmlns="http://www.w3.org/2000/svg" width="120" height="80"><rect width="120" height="80" fill="#7139db"/></svg>'
        elif path == '/data.json':
            time.sleep(0.2)
            mime, body = 'application/json', b'{"marker":"FETCH_OK"}'
        elif path == '/static.html':
            body = page('static', '<p id="result">STATIC_OK</p><img src="/image.svg" alt="test image">')
        elif path == '/delayed-dom.html':
            body = page('delayed-dom', '<p id="placeholder">Waiting</p><script>setTimeout(()=>{const p=document.createElement("p");p.id="result";p.textContent="DELAYED_OK";document.body.appendChild(p);},3000);</script>')
        elif path == '/fetch.html':
            body = page('fetch', '<p id="result">WAITING</p><script>fetch("/data.json").then(r=>r.json()).then(d=>document.querySelector("#result").textContent=d.marker);</script>')
        elif path == '/console.html':
            body = page('console', '<p id="result">CONSOLE_OK</p><script>console.log("LOG_OK");console.warn("WARN_OK");console.error("ERROR_OK");</script>')
        elif path == '/failed-resource.html':
            body = page('failed-resource', '<p id="result">FAILED_RESOURCE_OK</p><img src="/missing.png">')
        elif path == '/iframe.html':
            body = page('iframe', '<h1>Outer document</h1><iframe src="/inner.html"></iframe>')
        elif path == '/inner.html':
            body = page('inner', '<p id="result">IFRAME_OK</p>')
        elif path == '/dynamic.html':
            body = page('dynamic', '<p id="result">DYNAMIC_'+uuid.uuid4().hex+'</p><time>'+str(time.time())+'</time>')
        elif path == '/state.html':
            headers['Set-Cookie'] = 'fixture_server=SYNTHETIC; Path=/; SameSite=Lax'
            body = page('state', '''<p id="result"></p><script>
            console.log('INITIAL_EMPTY:'+String(localStorage.getItem('fixture')===null&&sessionStorage.getItem('fixture')===null));
            document.cookie='fixture_client=SYNTHETIC; Path=/; SameSite=Lax';
            localStorage.setItem('fixture','LOCAL_OK');sessionStorage.setItem('fixture','SESSION_OK');
            document.querySelector('#result').textContent=localStorage.getItem('fixture')+' '+sessionStorage.getItem('fixture')+' '+(document.cookie.includes('fixture_client=SYNTHETIC')&&document.cookie.includes('fixture_server=SYNTHETIC')?'COOKIE_OK':'COOKIE_FAIL');
            </script>''')
        else:
            code, mime, body = 404, 'text/plain', b'INTENTIONAL_NOT_FOUND'
        self.send_response(code)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        for k,v in headers.items(): self.send_header(k,v)
        self.end_headers()
        self.wfile.write(body)

def start():
    server = ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread = threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    return server, 'http://127.0.0.1:'+str(server.server_port)

if __name__ == '__main__':
    server, url = start()
    print(url,flush=True)
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        server.shutdown()
