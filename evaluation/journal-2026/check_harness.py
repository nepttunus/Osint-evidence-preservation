"""Smoke checks for fixture HTTP behaviour and DOM oracle, without a browser."""
import json
from urllib.request import urlopen
from urllib.error import HTTPError
from fixtures import start,CASES
from evaluate import MarkerParser

server,base=start()
try:
    for case in CASES:
        path='/redirect' if case=='redirect' else '/'+case+'.html'
        with urlopen(base+path) as r:
            assert r.status==200
            text=r.read().decode()
            assert '<!doctype html>' in text
            if case=='redirect':assert r.url.endswith('/static.html')
            if case=='delayed-dom':
                p=MarkerParser();p.feed(text)
                assert 'DELAYED_OK' not in p.text, 'Script literal must not satisfy DOM assertion'
    with urlopen(base+'/data.json') as r: assert json.load(r)['marker']=='FETCH_OK'
    try:urlopen(base+'/missing.png')
    except HTTPError as e:assert e.code==404
    else:raise AssertionError('Missing-resource fixture must return 404')
    print('PASS: 9 fixture routes; redirect; JSON fetch endpoint; intentional HTTP 404; delayed-DOM oracle excludes script literals.')
finally:server.shutdown();server.server_close()
