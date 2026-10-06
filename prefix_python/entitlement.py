from __future__ import annotations
import hashlib,hmac,json,os,secrets,socket,time,urllib.error,urllib.parse,urllib.request
from dataclasses import asdict,dataclass
from enum import Enum
from pathlib import Path
BASE="https://api.lemonsqueezy.com/v1/licenses"; VALIDATE_AFTER=7*86400; OFFLINE_GRACE=30*86400
class State(str,Enum):
 UNACTIVATED="UNACTIVATED"; ACTIVE_VALIDATED="ACTIVE_VALIDATED"; ACTIVE_CACHED="ACTIVE_CACHED"; OFFLINE_GRACE="OFFLINE_GRACE"; INVALID_KEY="INVALID_KEY"; WRONG_PRODUCT="WRONG_PRODUCT"; WRONG_VARIANT="WRONG_VARIANT"; ACTIVATION_LIMIT_REACHED="ACTIVATION_LIMIT_REACHED"; DEACTIVATED="DEACTIVATED"; REMOTE_VALIDATION_FAILED="REMOTE_VALIDATION_FAILED"; NETWORK_UNAVAILABLE="NETWORK_UNAVAILABLE"; CACHE_INVALID="CACHE_INVALID"; CACHE_EXPIRED="CACHE_EXPIRED"; UNKNOWN="UNKNOWN"; CONFIGURATION_REQUIRED="CONFIGURATION_REQUIRED"
ENTITLED={State.ACTIVE_VALIDATED,State.ACTIVE_CACHED,State.OFFLINE_GRACE}
@dataclass(frozen=True)
class Authority:
 store_id:int|None=None; product_id:int|None=None; variant_id:int|None=None
 def configured(self): return all(isinstance(x,int) and x>0 for x in (self.store_id,self.product_id,self.variant_id))
# Deliberately unset in this isolated branch. Owner must supply the public Lemon Squeezy IDs before release.
PRODUCTION_AUTHORITY=Authority()
@dataclass
class Status:
 state:str; entitled:bool; message:str; last_validated_at:int|None=None; instance_id:str|None=None; license_fingerprint:str|None=None; store_id:int|None=None; product_id:int|None=None; variant_id:int|None=None
 def to_dict(self): return asdict(self)
class TransportError(RuntimeError): pass
class ProtocolError(RuntimeError): pass
class Client:
 def __init__(self,opener=None,timeout=5): self.opener=opener or urllib.request.urlopen; self.timeout=timeout
 def post(self,action,fields):
  req=urllib.request.Request(f"{BASE}/{action}",data=urllib.parse.urlencode(fields).encode(),headers={"Accept":"application/json","Content-Type":"application/x-www-form-urlencoded"},method="POST")
  try:
   with self.opener(req,timeout=self.timeout) as r: raw=r.read()
  except (urllib.error.URLError,TimeoutError,socket.timeout,OSError) as e: raise TransportError(str(e)) from e
  try: out=json.loads(raw.decode())
  except Exception as e: raise ProtocolError("malformed JSON") from e
  if not isinstance(out,dict): raise ProtocolError("non-object JSON")
  return out
 def activate(self,k,n): return self.post("activate",{"license_key":k,"instance_name":n})
 def validate(self,k,i): return self.post("validate",{"license_key":k,"instance_id":i})
 def deactivate(self,k,i): return self.post("deactivate",{"license_key":k,"instance_id":i})
def root(platform=None,env=None):
 env=env or os.environ; platform=platform or os.name
 if env.get("PREFIX_ENTITLEMENT_ROOT"): return Path(env["PREFIX_ENTITLEMENT_ROOT"])
 if platform in ("nt","win32"): return Path(env.get("LOCALAPPDATA",str(Path.home()/"AppData"/"Local")))/"FastIndustries"/"PREFIX for Python"/"entitlement"
 base=Path(env.get("XDG_STATE_HOME",str(Path(env.get("HOME",str(Path.home())))/".local"/"state"))); return base/"fastindustries"/"prefix-python"/"entitlement"
def paths(r): return r/"entitlement.json",r/"license.key",r/"install.secret",r/"install.id"
def chmod(p,m):
 try:p.chmod(m)
 except OSError:pass
def ensure(r): r.mkdir(parents=True,exist_ok=True); chmod(r,0o700)
def install_id(r):
 ensure(r); p=paths(r)[3]
 if not p.exists(): p.write_text(secrets.token_hex(16)+"\n"); chmod(p,0o600)
 return p.read_text().strip()
def secret(r,create=False):
 p=paths(r)[2]
 if p.exists():
  try:return bytes.fromhex(p.read_text().strip())
  except Exception:return None
 if not create:return None
 ensure(r); b=secrets.token_bytes(32); p.write_text(b.hex()+"\n"); chmod(p,0o600); return b
def fp(k): return "sha256:"+hashlib.sha256(k.encode()).hexdigest()
def canon(d): return json.dumps(d,sort_keys=True,separators=(",",":")).encode()
def write(r,rec,k):
 ensure(r); rp,kp,_,_=paths(r); s=secret(r,True); body=dict(rec); body["integrity_hmac"]=hmac.new(s,canon(body),hashlib.sha256).hexdigest(); t=rp.with_suffix(".tmp"); t.write_text(json.dumps(body,indent=2,sort_keys=True)+"\n"); chmod(t,0o600); t.replace(rp); kp.write_text(k); chmod(kp,0o600)
def read(r):
 rp,kp,_,_=paths(r)
 if not rp.exists(): return None,None,None
 try: body=json.loads(rp.read_text()); k=kp.read_text(); s=secret(r)
 except Exception:return None,None,State.CACHE_INVALID
 if not isinstance(body,dict) or not k or s is None:return None,None,State.CACHE_INVALID
 sig=body.pop("integrity_hmac",None)
 if not isinstance(sig,str) or not hmac.compare_digest(sig,hmac.new(s,canon(body),hashlib.sha256).hexdigest()) or body.get("license_fingerprint")!=fp(k):return None,None,State.CACHE_INVALID
 return body,k,None
def msg(s): return {State.UNACTIVATED:"PREFIX is not activated.",State.ACTIVE_VALIDATED:"PREFIX is activated and validated.",State.ACTIVE_CACHED:"PREFIX is activated locally.",State.OFFLINE_GRACE:"PREFIX is operating within offline grace.",State.INVALID_KEY:"The license key is invalid or inactive.",State.WRONG_PRODUCT:"That key belongs to another product.",State.WRONG_VARIANT:"That key belongs to another PREFIX variant.",State.ACTIVATION_LIMIT_REACHED:"This license reached its activation limit.",State.DEACTIVATED:"PREFIX was deactivated here.",State.NETWORK_UNAVAILABLE:"The licensing service is unavailable.",State.REMOTE_VALIDATION_FAILED:"Remote validation failed.",State.CACHE_INVALID:"The local entitlement cache is invalid.",State.CACHE_EXPIRED:"The offline grace period expired.",State.CONFIGURATION_REQUIRED:"Commercial product identity is not configured in this build.",State.UNKNOWN:"Entitlement is unknown."}.get(s,s.value)
def identity(p,a):
 m=p.get("meta")
 if not isinstance(m,dict):return State.REMOTE_VALIDATION_FAILED
 if m.get("store_id")!=a.store_id or m.get("product_id")!=a.product_id:return State.WRONG_PRODUCT
 if m.get("variant_id")!=a.variant_id:return State.WRONG_VARIANT
 return None
def remote_bad(p):
 lk=p.get("license_key")
 if not isinstance(lk,dict):return State.REMOTE_VALIDATION_FAILED
 return State.INVALID_KEY if lk.get("status") in ("disabled","expired") else None
def status(r=None,now=None):
 r=r or root(); now=int(time.time() if now is None else now); rec,k,e=read(r)
 if e:return Status(e.value,False,msg(e))
 if rec is None:return Status(State.UNACTIVATED.value,False,msg(State.UNACTIVATED))
 last=rec.get("last_validated_at")
 if not isinstance(last,int) or last<0 or last>now+86400:return Status(State.CACHE_INVALID.value,False,msg(State.CACHE_INVALID))
 age=now-last; s=State.ACTIVE_CACHED if age<=VALIDATE_AFTER else State.OFFLINE_GRACE if age<=OFFLINE_GRACE else State.CACHE_EXPIRED
 return Status(s.value,s in ENTITLED,msg(s),last,rec.get("instance_id"),rec.get("license_fingerprint"),rec.get("store_id"),rec.get("product_id"),rec.get("variant_id"))
def activate(k,authority=PRODUCTION_AUTHORITY,client=None,r=None,now=None):
 k=k.strip(); r=r or root(); now=int(time.time() if now is None else now)
 if not authority.configured():return Status(State.CONFIGURATION_REQUIRED.value,False,msg(State.CONFIGURATION_REQUIRED))
 if len(k)<8:return Status(State.INVALID_KEY.value,False,msg(State.INVALID_KEY))
 try:p=(client or Client()).activate(k,"PREFIX-"+install_id(r))
 except TransportError:return Status(State.NETWORK_UNAVAILABLE.value,False,msg(State.NETWORK_UNAVAILABLE))
 except ProtocolError:return Status(State.REMOTE_VALIDATION_FAILED.value,False,msg(State.REMOTE_VALIDATION_FAILED))
 bad=identity(p,authority)
 if bad:return Status(bad.value,False,msg(bad))
 if not p.get("activated"):
  s=State.ACTIVATION_LIMIT_REACHED if "activation limit" in str(p.get("error","")).lower() else State.INVALID_KEY; return Status(s.value,False,msg(s))
 bad=remote_bad(p)
 if bad:return Status(bad.value,False,msg(bad))
 i=p.get("instance"); m=p.get("meta")
 if not isinstance(i,dict) or not isinstance(i.get("id"),str) or not isinstance(m,dict):return Status(State.REMOTE_VALIDATION_FAILED.value,False,msg(State.REMOTE_VALIDATION_FAILED))
 rec={"schema":1,"policy_version":1,"instance_id":i["id"],"install_id":install_id(r),"license_fingerprint":fp(k),"store_id":m["store_id"],"product_id":m["product_id"],"variant_id":m["variant_id"],"last_validated_at":now}; write(r,rec,k); return status(r,now)
def validate(authority=PRODUCTION_AUTHORITY,client=None,r=None,now=None,force=True):
 r=r or root(); now=int(time.time() if now is None else now); local=status(r,now)
 if not authority.configured():return Status(State.CONFIGURATION_REQUIRED.value,False,msg(State.CONFIGURATION_REQUIRED))
 rec,k,e=read(r)
 if e or rec is None or k is None:return local
 if not force and local.state==State.ACTIVE_CACHED.value:return local
 try:p=(client or Client()).validate(k,str(rec["instance_id"]))
 except (TransportError,ProtocolError):return local if local.entitled else Status(State.NETWORK_UNAVAILABLE.value,False,msg(State.NETWORK_UNAVAILABLE))
 bad=identity(p,authority)
 if bad:return Status(bad.value,False,msg(bad))
 if not p.get("valid") or remote_bad(p):return Status(State.REMOTE_VALIDATION_FAILED.value,False,str(p.get("error") or msg(State.REMOTE_VALIDATION_FAILED)))
 inst=p.get("instance")
 if not isinstance(inst,dict) or inst.get("id")!=rec.get("instance_id"):return Status(State.REMOTE_VALIDATION_FAILED.value,False,msg(State.REMOTE_VALIDATION_FAILED))
 rec["last_validated_at"]=now; write(r,rec,k); s=status(r,now); s.state=State.ACTIVE_VALIDATED.value; s.message=msg(State.ACTIVE_VALIDATED); return s
def deactivate(authority=PRODUCTION_AUTHORITY,client=None,r=None):
 r=r or root(); rec,k,e=read(r)
 if e:return Status(e.value,False,msg(e))
 if rec is None or k is None:return Status(State.UNACTIVATED.value,False,msg(State.UNACTIVATED))
 if not authority.configured():return Status(State.CONFIGURATION_REQUIRED.value,False,msg(State.CONFIGURATION_REQUIRED))
 try:p=(client or Client()).deactivate(k,str(rec["instance_id"]))
 except TransportError:return Status(State.NETWORK_UNAVAILABLE.value,False,msg(State.NETWORK_UNAVAILABLE))
 except ProtocolError:return Status(State.REMOTE_VALIDATION_FAILED.value,False,msg(State.REMOTE_VALIDATION_FAILED))
 bad=identity(p,authority)
 if bad:return Status(bad.value,False,msg(bad))
 if not p.get("deactivated"):return Status(State.REMOTE_VALIDATION_FAILED.value,False,str(p.get("error") or msg(State.REMOTE_VALIDATION_FAILED)))
 for q in paths(r)[:2]:
  try:q.unlink()
  except FileNotFoundError:pass
 return Status(State.DEACTIVATED.value,False,msg(State.DEACTIVATED))
def require(r=None): return status(r)
