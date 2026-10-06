from __future__ import annotations
import json,os,subprocess,sys,tempfile,time,unittest
from pathlib import Path
from prefix_python.entitlement import fp,write
ROOT=Path(__file__).resolve().parents[1]
class EntitlementGateTests(unittest.TestCase):
 def run_cli(self,root,*args):
  env=os.environ.copy();env["PREFIX_ENTITLEMENT_ROOT"]=str(root)
  return subprocess.run([sys.executable,"-m","prefix_python",*args],cwd=ROOT,env=env,text=True,capture_output=True,check=False)
 def seed(self,root):
  key="test-only-entitled-key"; now=int(time.time())
  write(root,{"schema":1,"policy_version":1,"instance_id":"test-instance","install_id":"test-install","license_fingerprint":fp(key),"store_id":11,"product_id":22,"variant_id":33,"last_validated_at":now},key)
 def test_unentitled_apply_never_mutates(self):
  with tempfile.TemporaryDirectory() as t:
   base=Path(t); ent=base/"ent"; target=base/"sample.py"; original="if ready\nprint('x')\n";target.write_text(original)
   c=self.run_cli(ent,str(target),"--apply","--json");self.assertEqual(c.returncode,3,c.stderr);p=json.loads(c.stdout);self.assertEqual(p["refusal_code"],"entitlement_required");self.assertFalse(p["mutation_performed"]);self.assertEqual(target.read_text(),original)
 def test_entitled_apply_preserves_existing_correction(self):
  with tempfile.TemporaryDirectory() as t:
   base=Path(t);ent=base/"ent";self.seed(ent);target=base/"sample.py";target.write_text("if ready\nprint('x')\n")
   c=self.run_cli(ent,str(target),"--apply","--json");self.assertEqual(c.returncode,0,c.stderr);p=json.loads(c.stdout);self.assertEqual(p["status"],"ACCEPT_FIXED");self.assertEqual(target.read_text(),"if ready:\n    print('x')\n")
if __name__=="__main__":unittest.main()
