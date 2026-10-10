from __future__ import annotations
import argparse,getpass,json,sys,warnings
from .entitlement import activate,deactivate,status,validate

def main(argv=None):
 p=argparse.ArgumentParser(prog='prefix-python license',description='Manage the local PREFIX for Python entitlement.')
 p.add_argument('operation',choices=['status','activate','validate','deactivate'])
 p.add_argument('--stdin',action='store_true',help='Read the activation key from standard input, never from command-line arguments.')
 p.add_argument('--json',action='store_true'); a,unknown=p.parse_known_args(argv)
 if unknown:p.error('unsupported arguments; activation keys must use hidden input or --stdin')
 if a.stdin and a.operation!='activate':p.error('--stdin is only valid with activate')
 if a.operation=='activate':
  if a.stdin:
   raw=sys.stdin.readline(4097)
   if len(raw)>4096:p.error('activation input is too long')
   key=raw.strip()
  else:
   try:
    with warnings.catch_warnings():
     warnings.simplefilter('error',getpass.GetPassWarning)
     key=getpass.getpass('PREFIX license key: ').strip()
   except (getpass.GetPassWarning,EOFError,KeyboardInterrupt):
    p.error('a hidden input terminal is required; use --stdin for editor integration')
  if not key:p.error('activate requires a license key through hidden input or --stdin')
  out=activate(key)
 elif a.operation=='validate':out=validate()
 elif a.operation=='deactivate':out=deactivate()
 else:out=status()
 payload=out.to_dict()
 if a.json:sys.stdout.write(json.dumps(payload,indent=2,sort_keys=True)+'\n')
 else:
  sys.stdout.write(f"{payload['state']}\n{payload['message']}\n")
  if payload['entitled']:sys.stdout.write('PREFIX commercial capability is authorized on this installation.\n')
 return 0 if out.entitled or a.operation in ('status','deactivate') else 3
