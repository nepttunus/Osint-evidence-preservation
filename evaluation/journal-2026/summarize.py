"""Create reviewable tables from observed results, retaining all failed attempts."""
import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path
from statistics import median

def summarize(root):
    root=Path(root)
    if not (root/'results.json').exists():
        status=json.loads((root/'status.json').read_text())
        (root/'summary.md').write_text('# Evaluation status\n\n'+status['status']+'\n\n'+status.get('reason','')+'\n')
        return
    results=json.loads((root/'results.json').read_text())
    fields=['corpus','id','repetition','url','capture_completed','directory_ok','zip_ok','fixture_all_passed','http_status','possible_block_page','capture_seconds','zip_bytes','error']
    with (root/'results.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for r in results:
            row={k:r.get(k) for k in fields}
            row.update(directory_ok=r.get('original_directory',{}).get('ok'),zip_ok=r.get('original_zip',{}).get('ok'),fixture_all_passed=r.get('fixture',{}).get('all_passed'),http_status=r.get('metadata',{}).get('http_status'))
            writer.writerow(row)
    lines=['# Observed evaluation results','','Counts refer to attempts; repetitions of one site are not independent sites. Cryptographic validity is distinct from acquisition completeness. Live content requires review.','', '| Corpus | Attempts | Captures completed | Original directory / ZIP accepted | Fixture runs meeting assertions |','|---|---:|---:|---:|---:|']
    for corpus in ['fixture','live']:
        group=[r for r in results if r['corpus']==corpus]
        if not group:continue
        completed=sum(r.get('capture_completed',False) for r in group)
        ver=sum(r.get(key,{}).get('ok') is True for r in group for key in ['original_directory','original_zip'])
        nver=sum(key in r for r in group for key in ['original_directory','original_zip'])
        fp=sum(r.get('fixture',{}).get('all_passed',False) for r in group)
        lines.append(f'| {corpus} | {len(group)} | {completed} | {ver}/{nver} | {str(fp)+"/"+str(len(group)) if corpus=="fixture" else "not assessed"} |')
        times=[r['capture_seconds'] for r in group if 'capture_seconds' in r]
        if times:lines.extend(['',f'{corpus} observed capture times: median {median(times):.3f} s; range {min(times):.3f}–{max(times):.3f} s. Concurrent execution; not a controlled performance benchmark.',''])
    variants=defaultdict(list)
    for r in results:
        for t in r.get('tampering',[]):variants[t['variant']].append(t)
    lines += ['', '| Tamper variant | Rejected / constructed checks |','|---|---:|']
    for v,items in variants.items():lines.append(f'| {v} | {sum(x["rejected"] for x in items)}/{len(items)} |')
    lines+=['','## Per-fixture assertions','','| Fixture | Complete captures | All assertions met |','|---|---:|---:|']
    for case in sorted(set(r['id'] for r in results if r['corpus']=='fixture')):
        g=[r for r in results if r['corpus']=='fixture' and r['id']==case]
        lines.append(f'| {case} | {sum(r.get("capture_completed",False) for r in g)}/{len(g)} | {sum(r.get("fixture",{}).get("all_passed",False) for r in g)}/{len(g)} |')
    dynamic=[r.get('fixture',{}).get('dom_marker') for r in results if r['corpus']=='fixture' and r['id']=='dynamic' and r.get('fixture',{}).get('all_passed')]
    if dynamic:lines += ['',f'Dynamic markers: {len(set(dynamic))} unique in {len(dynamic)} completed, assertion-passing captures.']
    (root/'summary.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('results');summarize(p.parse_args().results)
