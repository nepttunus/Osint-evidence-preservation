"""Evaluate an unmodified checkout. No external accounts, extension, or login required."""
from __future__ import annotations
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import traceback
from urllib.parse import urlsplit
import zipfile

HERE=Path(__file__).resolve().parent
ARTIFACTS=['capture_metadata.json','http_metadata.json','console_logs.json','network.har','page.html','page.pdf','screenshot.png','trace.zip']
VARIANTS=['artifact_modified','artifact_removed','manifest_modified','artifact_and_digest_modified','signature_removed','artifact_digest_modified_signature_removed']

def write(path,obj):
    Path(path).write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')

class MarkerParser(HTMLParser):
    def __init__(self):
        super().__init__();self.inside=False;self.text=''
    def handle_starttag(self,tag,attrs):
        if dict(attrs).get('id')=='result':self.inside=True
    def handle_endtag(self,tag):
        if tag=='p':self.inside=False
    def handle_data(self,data):
        if self.inside:self.text+=data

def checks(case,run):
    from PIL import Image
    from pypdf import PdfReader
    html=(run/'artifacts/page.html').read_text()
    parser=MarkerParser();parser.feed(html); marker=parser.text
    pdf='\n'.join(p.extract_text() or '' for p in PdfReader(run/'artifacts/page.pdf').pages)
    har=json.loads((run/'artifacts/network.har').read_text())['log']['entries']
    logs=json.loads((run/'artifacts/console_logs.json').read_text())
    meta=json.loads((run/'artifacts/http_metadata.json').read_text())
    def request(path,status):
        return any(urlsplit(e['request']['url']).path==path and e['response']['status']==status for e in har)
    def message(kind,text): return any(x['type']==kind and x['text']==text for x in logs)
    expected={'static':'STATIC_OK','redirect':'STATIC_OK','delayed-dom':'DELAYED_OK','fetch':'FETCH_OK','console':'CONSOLE_OK','failed-resource':'FAILED_RESOURCE_OK','iframe':'IFRAME_OK','dynamic':'DYNAMIC_','state':'LOCAL_OK SESSION_OK COOKIE_OK'}[case]
    pixels=Counter(Image.open(run/'artifacts/screenshot.png').convert('RGB').getdata())
    assertions={'pdf_marker':expected in pdf,'screenshot_marker_background':pixels[(17,199,83)]>1000}
    if case!='iframe': assertions['dom_marker']=expected in marker
    if case in ('static','redirect'):
        assertions.update(css_recorded=request('/style.css',200),image_recorded=request('/image.svg',200),screenshot_image_color=pixels[(113,57,219)]>1000)
    if case=='redirect': assertions.update(redirect_recorded=request('/redirect',302),final_url=urlsplit(meta['final_url']).path=='/static.html')
    if case=='fetch': assertions['fetch_recorded']=request('/data.json',200)
    if case=='console': assertions.update(log_recorded=message('log','LOG_OK'),warning_recorded=message('warning','WARN_OK'),error_recorded=message('error','ERROR_OK'))
    if case=='failed-resource':assertions['http_404_recorded']=request('/missing.png',404)
    if case=='iframe':assertions['iframe_request']=request('/inner.html',200)
    if case=='state':assertions['fresh_storage']=message('log','INITIAL_EMPTY:true')
    return {'assertions':assertions,'all_passed':all(assertions.values()),'dom_marker':marker,'iframe_text_in_top_level_html':('IFRAME_OK' in html) if case=='iframe' else None,'note':'Screenshot color checks confirm controlled rendered regions, not general visual fidelity; trace presence is checked but trace contents are not asserted.'}

def verify_record(target):
    from engine.src.verify import verify_path
    start=time.perf_counter()
    try: result=asdict(verify_path(target));result['exception']=None
    except Exception as e:result={'ok':None,'errors':[],'checked_files':None,'exception':type(e).__name__+': '+str(e)}
    result['seconds']=time.perf_counter()-start
    return result

def tamper(run):
    from engine.src.package import create_zip_archive
    output=[]
    for variant in VARIANTS:
        with tempfile.TemporaryDirectory() as td:
            copy=Path(td)/'copy'
            shutil.copytree(run,copy,ignore=shutil.ignore_patterns('evidence_bundle.zip'))
            artifact=copy/'artifacts/page.html'
            mf=copy/'manifest.json';manifest=json.loads(mf.read_text())
            if variant in ['artifact_modified','artifact_and_digest_modified','artifact_digest_modified_signature_removed']:
                artifact.write_bytes(artifact.read_bytes()+b'\n<!-- CONTROLLED_TAMPERING -->')
            if variant=='artifact_removed':artifact.unlink()
            if variant=='manifest_modified':manifest['capture']['page_title']='CONTROLLED_MANIFEST_CHANGE'
            if variant in ['artifact_and_digest_modified','artifact_digest_modified_signature_removed']:
                for entry in manifest['files']:
                    if entry['path']=='artifacts/page.html':
                        entry['sha256']=hashlib.sha256(artifact.read_bytes()).hexdigest();entry['size_bytes']=artifact.stat().st_size
            if variant in ['manifest_modified','artifact_and_digest_modified','artifact_digest_modified_signature_removed']:write(mf,manifest)
            if variant in ['signature_removed','artifact_digest_modified_signature_removed']:(copy/'manifest.sig').unlink()
            for form,target in [('directory',copy),('zip',create_zip_archive(copy))]:
                result=verify_record(target)
                output.append({'variant':variant,'form':form,'rejected':result['ok'] is False,**result})
    return output

def worker(args):
    sys.path.insert(0,str(Path(args.repo).resolve()))
    from engine.src.service import run_capture_job
    result={'id':args.case,'url':args.url,'corpus':args.kind,'repetition':args.repetition,'started_at':datetime.now(timezone.utc).isoformat()}
    start=time.perf_counter()
    try:
        payload=run_capture_job(args.url,Path(args.output)/'capture',timeout_ms=30000,actor='journal-evaluation')
        result['capture_seconds']=time.perf_counter()-start
        run=Path(payload['run_dir']);result['run_dir']=str(run)
        result['capture_completed']=True
        result['artifacts']={a:(run/'artifacts'/a).exists() and (run/'artifacts'/a).stat().st_size>0 for a in ARTIFACTS}
        result['original_directory']=verify_record(run);result['original_zip']=verify_record(Path(payload['zip']))
        result['zip_bytes']=Path(payload['zip']).stat().st_size
        with zipfile.ZipFile(payload['zip']) as z:
            result['private_key_absent']=not any('private_key' in n for n in z.namelist())
        result['metadata']=json.loads((run/'artifacts/http_metadata.json').read_text())
        result['metadata'].pop('response_headers',None)
        result['tampering']=tamper(run)
        if args.kind=='fixture':result['fixture']=checks(args.case,run)
        else:
            title=result['metadata'].get('page_title','').lower()
            result['possible_block_page']=any(s in title for s in ['access denied','just a moment','attention required','site unavailable','robot','captcha'])
            result['content_review']='pending; HTTP success and integrity do not establish target-page completeness'
    except Exception as e:
        result.setdefault('capture_completed',False)
        result['error']=type(e).__name__+': '+str(e)
        result['traceback']=traceback.format_exc()
    result['total_seconds']=time.perf_counter()-start
    write(Path(args.output)/'result.json',result)
    print(json.dumps({k:result.get(k) for k in ['id','corpus','repetition','capture_completed','error']}),flush=True)

def main(args):
    from fixtures import start,CASES
    repo=Path(args.repo).resolve();output=Path(args.output).resolve();output.mkdir(parents=True,exist_ok=False)
    server,base=start()
    env={'started_at':datetime.now(timezone.utc).isoformat(),'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),'git_status':subprocess.check_output(['git','status','--short'],cwd=repo,text=True),'python':sys.version,'platform':platform.platform(),'cpu_count':os.cpu_count(),'workers':args.workers,'repetitions':args.repetitions,'navigation_policy':'unmodified engine: networkidle, timeout 30000 ms; no added observation window','process_timeout_seconds':90,'viewport':'Playwright default 1280x720','locale':'Playwright default en-US','timezone':'browser system default','https_errors':'ignored by original engine','fixtures_sha256':hashlib.sha256((HERE/'fixtures.py').read_bytes()).hexdigest(),'corpus_sha256':hashlib.sha256((HERE/'corpus.json').read_bytes()).hexdigest(),'dependencies':{x.metadata['Name']:x.version for x in importlib.metadata.distributions()}}
    env['tracked_diff_sha256']=hashlib.sha256(subprocess.check_output(['git','diff','HEAD'],cwd=repo)).hexdigest()
    env['engine_files_sha256']={str(f.relative_to(repo)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted((repo/'engine').rglob('*.py'))}
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            b=pw.chromium.launch();env['browser_version']=b.version;b.close()
    except Exception as e:
        env['browser_preflight_error']=str(e);write(output/'environment.json',env)
        write(output/'status.json',{'status':'blocked_before_capture','reason':'Chromium unavailable; no capture attempts or live-site results fabricated'})
        server.shutdown();print(env['browser_preflight_error']);return 2
    write(output/'environment.json',env)
    targets=[]
    if args.mode in ('all','fixtures'):
        targets += [{'id':c,'url':base+('/redirect' if c=='redirect' else '/'+c+'.html'),'corpus':'fixture'} for c in CASES]
    if args.mode in ('all','live'):
        targets += [{**x,'corpus':'live'} for x in json.loads((HERE/'corpus.json').read_text())]
    jobs=[{**x,'repetition':r} for x in targets for r in range(1,args.repetitions+1)]
    write(output/'schedule.json',jobs)
    def launch(job):
        out=output/(job['corpus']+'-'+job['id']+'-'+str(job['repetition']));out.mkdir()
        cmd=[sys.executable,str(HERE/'evaluate.py'),'--worker','--repo',str(repo),'--output',str(out),'--case',job['id'],'--url',job['url'],'--kind',job['corpus'],'--repetition',str(job['repetition'])]
        with (out/'worker.log').open('w') as log:
            proc=subprocess.Popen(cmd,stdout=log,stderr=log,start_new_session=True)
            try:proc.wait(timeout=90)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGKILL);proc.wait()
                write(out/'result.json',{**job,'capture_completed':False,'error':'worker_timeout_90s'})
        if not (out/'result.json').exists():write(out/'result.json',{**job,'capture_completed':False,'error':'worker_exit_'+str(proc.returncode)})
        result=json.loads((out/'result.json').read_text())
        print(job['corpus'],job['id'],job['repetition'],'capture=',result.get('capture_completed'),'fixture=',result.get('fixture',{}).get('all_passed'),flush=True)
        return result
    results=[]
    try:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            for future in as_completed([pool.submit(launch,j) for j in jobs]):results.append(future.result())
    finally:server.shutdown();server.server_close()
    results.sort(key=lambda r:(r['corpus'],r['id'],r['repetition']))
    write(output/'results.json',results)
    write(output/'status.json',{'status':'completed','attempts':len(results),'capture_completed':sum(x.get('capture_completed',False) for x in results),'finished_at':datetime.now(timezone.utc).isoformat()})
    from summarize import summarize
    summarize(output)
    return 0

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo',required=True);ap.add_argument('--output',required=True)
    ap.add_argument('--mode',choices=['all','fixtures','live'],default='all')
    ap.add_argument('--repetitions',type=int,default=3);ap.add_argument('--workers',type=int,default=3)
    ap.add_argument('--worker',action='store_true');ap.add_argument('--case');ap.add_argument('--url');ap.add_argument('--kind');ap.add_argument('--repetition',type=int)
    args=ap.parse_args()
    if args.worker:worker(args)
    else:sys.exit(main(args))
