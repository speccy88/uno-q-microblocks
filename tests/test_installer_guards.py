# SPDX-License-Identifier: MIT
"""Installer guard tests with simulated OpenOCD; zero hardware writes."""
import argparse,hashlib,importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
R=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('installer',R/'tools/install_runtime.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.r=Path(self.tmp.name);self.loader=self.r/'loader.elf';self.loader.write_bytes(b'simulated loader');self.loader_sha=m.sha(self.loader)
  b=bytearray(64);b[:6]=b'\x7fELF\x01\x01';b[18:20]=b'\x28\x00';self.image=self.r/'smallvm_unoq.ino.elf-zsk.bin';self.image.write_bytes(b)
  self.meta=self.r/'image.json';self.record={'preserves_pacoblaze':False,'module_bytes':64,'module_sha256':m.sha(self.image),'loader_sha256':self.loader_sha};self.meta.write_text(json.dumps(self.record));self.calls=[]
 def tearDown(self):self.tmp.cleanup()
 def run_install(self,fail=False,truncated=False):
  recovery=self.r/'private';baseline=b'P'*(m.CAPACITY if not truncated else 32)
  def fake(argv,**kwargs):
   body=Path(argv[-1]).read_text();self.calls.append(body)
   if 'dump_image' in body:(recovery/'before-install-768KiB.bin').write_bytes(baseline)
   if fail and 'flash write_image erase' in body and 'smallvm_unoq' in body:return subprocess.CompletedProcess(argv,1,'','simulated verify failure')
   return subprocess.CompletedProcess(argv,0,'simulated OpenOCD','')
  args=['installer','--install',str(self.meta),'--loader',str(self.loader),'--recovery-dir',str(recovery)]
  with patch.object(sys,'argv',args),patch.object(m.os,'geteuid',return_value=0),patch.object(m,'LOADER_SHA',self.loader_sha),patch.object(m.subprocess,'run',side_effect=fake):m.main()
 def test_success_is_application_only(self):
  self.run_install();self.assertEqual(len(self.calls),2);self.assertNotIn('0x080',self.calls[-1]);self.assertIn('0x08100000 bin',self.calls[-1])
 def test_bad_checksum_no_commands(self):
  self.image.write_bytes(b'bad')
  with self.assertRaises(RuntimeError):self.run_install()
  self.assertEqual(self.calls,[])
 def test_truncated_backup_prevents_write(self):
  with self.assertRaises(RuntimeError):self.run_install(truncated=True)
  self.assertEqual(len(self.calls),1);self.assertNotIn('flash write_image',self.calls[0])
 def test_failed_install_restores_full_backup(self):
  with self.assertRaises(RuntimeError):self.run_install(fail=True)
  self.assertEqual(len(self.calls),3);self.assertIn('before-install-768KiB.bin',self.calls[-1]);self.assertNotIn('0x080',self.calls[-1])
 def test_path_injection_rejected(self):
  with self.assertRaises(RuntimeError):m.safe_path(self.r/'bad} reset {')
if __name__=='__main__':unittest.main(verbosity=2)
