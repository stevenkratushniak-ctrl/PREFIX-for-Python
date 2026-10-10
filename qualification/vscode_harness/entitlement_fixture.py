"""Test-only local licensing fixtures. Never shipped inside the VSIX or wheel."""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path
from prefix_python import entitlement as e

scenario=sys.argv[1]
target=e.root()
for file in e.paths(target)[:2]:
    file.unlink(missing_ok=True)
if scenario in ("active","expired"):
    authority=e.PRODUCTION_AUTHORITY
    if not authority.configured():
        authority=e.Authority(476739,1416057,2212018)
    class SyntheticClient:
        def activate(self,key,name):
            return {"activated":True,"license_key":{"status":"active"},"instance":{"id":"synthetic-host-instance"},"meta":{"store_id":authority.store_id,"product_id":authority.product_id,"variant_id":authority.variant_id}}
    when=int(time.time())-(e.OFFLINE_GRACE+86400) if scenario=="expired" else int(time.time())
    result=e.activate("PREFIX-SYNTHETIC-HOST-FIXTURE",authority=authority,client=SyntheticClient(),r=target,now=when)
    assert result.entitled, result.state
elif scenario=="invalid":
    target.mkdir(parents=True,exist_ok=True)
    e.paths(target)[0].write_text('{"invalid":"synthetic-corrupt-cache"}',encoding="utf-8")
elif scenario!="unactivated":
    raise ValueError("unknown fixture scenario")
state=e.status(r=target)
print(json.dumps({"scenario":scenario,"state":state.state,"entitled":state.entitled,"synthetic":True}))
