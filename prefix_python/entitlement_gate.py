from __future__ import annotations
import json,sys
from .entitlement import require

def gate(argv:list[str])->int|None:
    if '--version' in argv or '--help' in argv or '-h' in argv: return None
    st=require()
    if st.entitled: return None
    payload={'accepted':False,'changed':False,'mutation_performed':False,'wrote':False,'status':'REFUSE_INVALID','state':'REFUSED','lane':'ANALYZE','refusal_code':'entitlement_required','refusal_reason':st.message,'entitlement':st.to_dict(),'source':'','events':[],'candidates':[],'receipt_path':None}
    if '--json' in argv: sys.stdout.write(json.dumps(payload,indent=2,sort_keys=True)+'\n')
    else: sys.stdout.write('PREFIX activation required.\n'+st.message+'\nRun `prefix-python license status` or activate a purchased license.\n')
    return 3
