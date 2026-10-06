from __future__ import annotations
import argparse,json,sys
from .entitlement import activate,deactivate,status,validate

def main(argv=None):
 p=argparse.ArgumentParser(prog='prefix-python license',description='Manage the local PREFIX for Python entitlement.')
 p.add_argument('operation',choices=['status','activate','validate','deactivate']); p.add_argument('license_key',nargs='?'); p.add_argument('--json',action='store_true'); a=p.parse_args(argv)
 if a.operation=='activate':
  if not a.license_key:p.error('activate requires a license key')
  out=activate(a.license_key)
 elif a.operation=='validate':out=validate()
 elif a.operation=='deactivate':out=deactivate()
 else:out=status()
 payload=out.to_dict()
 if a.json:sys.stdout.write(json.dumps(payload,indent=2,sort_keys=True)+'\n')
 else:
  sys.stdout.write(f"{payload['state']}\n{payload['message']}\n")
  if payload['entitled']:sys.stdout.write('PREFIX commercial capability is authorized on this installation.\n')
 return 0 if out.entitled or a.operation in ('status','deactivate') else 3
