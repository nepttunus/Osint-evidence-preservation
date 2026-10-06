"""Browser-independent audit using real repository signing/packaging/verifying functions.

These synthetic files are NOT Web captures and provide NO acquisition evidence.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from evaluate import tamper,verify_record,write

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo',required=True);ap.add_argument('--output',required=True)
    args=ap.parse_args();repo=Path(args.repo).resolve();sys.path.insert(0,str(repo))
    from engine.src.manifest import build_manifest
    from engine.src.signature import ensure_keypair,sign_manifest
    from engine.src.package import create_zip_archive
    output=Path(args.output).resolve();output.mkdir(parents=True,exist_ok=False)
    records=[]
    for repetition in range(1,4):
        run=output/f'synthetic-{repetition}';(run/'artifacts').mkdir(parents=True)
        (run/'artifacts/page.html').write_text('<!doctype html><title>Synthetic integrity audit</title><p>NOT A BROWSER CAPTURE</p>')
        private,public=ensure_keypair(output/'_private_keys'/str(repetition))
        (run/'keys').mkdir();shutil.copy2(public,run/'keys/public_key.pem')
        _,manifest=build_manifest(run,{'source_url':'synthetic:no-browser','page_title':'Synthetic integrity audit','repetition':repetition})
        sign_manifest(manifest,private,run/'manifest.sig')
        archive=create_zip_archive(run)
        records.append({'repetition':repetition,'original_directory':verify_record(run),'original_zip':verify_record(archive),'tampering':tamper(run)})
    variants=[x for r in records for x in r['tampering']]
    summary={'executed_at':datetime.now(timezone.utc).isoformat(),'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),'kind':'browser-independent synthetic integrity audit; not capture validation','repetitions':3,'original_checks':6,'original_accepted':sum(r[f]['ok'] is True for r in records for f in ['original_directory','original_zip']),'tampered_checks':len(variants),'tampered_rejected':sum(x['rejected'] for x in variants),'by_variant':{v:{'total':sum(x['variant']==v for x in variants),'rejected':sum(x['variant']==v and x['rejected'] for x in variants)} for v in sorted(set(x['variant'] for x in variants))},'records':records}
    summary['git_status']=subprocess.check_output(['git','status','--short'],cwd=repo,text=True)
    summary['tracked_diff_sha256']=hashlib.sha256(subprocess.check_output(['git','diff','HEAD'],cwd=repo)).hexdigest()
    summary['engine_files_sha256']={str(f.relative_to(repo)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted((repo/'engine').rglob('*.py'))}
    write(output/'integrity-audit.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k!='records'},indent=2))

if __name__=='__main__':main()
