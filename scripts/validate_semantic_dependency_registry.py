#!/usr/bin/env python3
"""Stdlib validator for the semantic dependency obligation registry."""
import argparse, json, sys
from pathlib import Path
PIN='de36f2ec1f9c530080eff7929ae28229f45da069'
REQUIRED={'schema_version','pinned_upstream','claim_boundary','entries'}
ENTRY={'id','source_anchor','adequate_key_requires','invalidation_fail_closed','known_counterexample','evidence_status','evidence_note'}
CATEGORIES={'successful-name-lookups','negative-name-lookups','import-export-views','shadowing','aliases-refinements','source-origins','options-builtins','plugins-rewriters','cancellation','module-roster'}
def validate(doc):
 e=[]
 if not isinstance(doc,dict) or not REQUIRED<=doc.keys(): return ['missing required top-level fields']
 if doc['schema_version']!=1: e.append('unsupported schema_version')
 if doc['pinned_upstream'].get('revision')!=PIN: e.append('pinned revision mismatch')
 if 'not established' not in doc['claim_boundary']: e.append('claim boundary must disclaim completeness')
 if not isinstance(doc['entries'],list): return e+['entries must be an array']
 ids=set()
 for i,x in enumerate(doc['entries']):
  w=f'entries[{i}]'
  if not isinstance(x,dict) or not ENTRY<=x.keys(): e.append(f'{w}: missing required fields'); continue
  if x['id'] in ids: e.append(f'{w}: duplicate id')
  ids.add(x['id'])
  a=x['source_anchor']
  if not isinstance(a,dict) or not a.get('files') or not a.get('csharp_symbol'): e.append(f'{w}: anchor must include files and known symbol or explicit unknown')
  elif 'unknown' in a['csharp_symbol'].lower() and not a['csharp_symbol'].startswith('unknown:'): e.append(f'{w}: unknown anchor must be explicit')
  for k in ('adequate_key_requires','invalidation_fail_closed','known_counterexample','evidence_note'):
   if not isinstance(x[k],str) or not x[k].strip(): e.append(f'{w}: {k} must be nonempty')
  if x['evidence_status'] not in {'measured','abstract','unverified'}: e.append(f'{w}: invalid evidence_status')
 missing=CATEGORIES-ids
 if missing: e.append('missing categories: '+', '.join(sorted(missing)))
 return e
def main():
 p=argparse.ArgumentParser(); p.add_argument('registry',nargs='?',type=Path,default=Path(__file__).resolve().parents[1]/'research/semantic-dependency-registry.json'); a=p.parse_args()
 try: d=json.loads(a.registry.read_text())
 except (OSError,json.JSONDecodeError) as ex: print(ex,file=sys.stderr); return 2
 errors=validate(d)
 if errors: print('\n'.join(errors)); return 1
 print(f"semantic dependency registry valid: {len(d['entries'])} obligations (incomplete by design)"); return 0
if __name__=='__main__': raise SystemExit(main())
