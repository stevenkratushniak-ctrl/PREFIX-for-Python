import json,tempfile,unittest
from pathlib import Path
from prefix_python.entitlement import Authority,State,activate,deactivate,status,validate,OFFLINE_GRACE,VALIDATE_AFTER
A=Authority(11,22,33)
def response(**over):
 d={'activated':True,'valid':True,'deactivated':True,'error':None,'license_key':{'id':9,'status':'active','activation_limit':3,'activation_usage':1,'expires_at':None},'instance':{'id':'instance-1','name':'PREFIX-test'},'meta':{'store_id':11,'product_id':22,'variant_id':33}}
 d.update(over); return d
class Fake:
 def __init__(self,a=None,v=None,d=None): self.a=a or response(); self.v=v or response(); self.d=d or response()
 def activate(self,k,n): return self.a
 def validate(self,k,i): return self.v
 def deactivate(self,k,i): return self.d
class EntitlementTests(unittest.TestCase):
 def test_activation_cache_grace_and_expiry(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t); self.assertTrue(activate('legit-key-123',A,Fake(),r,1000).entitled); self.assertEqual(status(r,1000).state,State.ACTIVE_CACHED.value); self.assertEqual(status(r,1000+VALIDATE_AFTER+1).state,State.OFFLINE_GRACE.value); self.assertFalse(status(r,1000+OFFLINE_GRACE+1).entitled)
 def test_wrong_product_variant_and_limit(self):
  with tempfile.TemporaryDirectory() as t:
   p=response();p['meta']['product_id']=999;self.assertEqual(activate('legit-key-123',A,Fake(a=p),Path(t),1000).state,State.WRONG_PRODUCT.value)
  with tempfile.TemporaryDirectory() as t:
   p=response();p['meta']['variant_id']=999;self.assertEqual(activate('legit-key-123',A,Fake(a=p),Path(t),1000).state,State.WRONG_VARIANT.value)
  with tempfile.TemporaryDirectory() as t:
   p=response(activated=False,error='This license key has reached the activation limit.');self.assertEqual(activate('legit-key-123',A,Fake(a=p),Path(t),1000).state,State.ACTIVATION_LIMIT_REACHED.value)
 def test_tamper_and_backward_clock(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);activate('legit-key-123',A,Fake(),r,1000);p=r/'entitlement.json';d=json.loads(p.read_text());d['product_id']=999;p.write_text(json.dumps(d));self.assertEqual(status(r,1000).state,State.CACHE_INVALID.value)
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);activate('legit-key-123',A,Fake(),r,100000);self.assertEqual(status(r,1).state,State.CACHE_INVALID.value)
 def test_validate_instance_and_deactivate(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);activate('legit-key-123',A,Fake(),r,1000);self.assertEqual(validate(A,Fake(),r,2000).state,State.ACTIVE_VALIDATED.value);self.assertEqual(deactivate(A,Fake(),r).state,State.DEACTIVATED.value);self.assertEqual(status(r).state,State.UNACTIVATED.value)
 def test_replayed_wrong_instance_refused(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);activate('legit-key-123',A,Fake(),r,1000);p=response();p['instance']['id']='other';self.assertEqual(validate(A,Fake(v=p),r,2000).state,State.REMOTE_VALIDATION_FAILED.value)
if __name__=='__main__':unittest.main()
