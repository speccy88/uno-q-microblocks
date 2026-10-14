from pathlib import Path
import shutil,difflib
from fix_runtime import fix
root=Path(__file__).resolve().parents[1]
src=root/'sources/smallvm/vm'; dst=root/'build/smallvm_unoq/src/vm'; dst.mkdir(parents=True,exist_ok=True)
files=['interp.c','interp.h','mem.c','mem.h','runtime.c','persist.c','persist.h','dataPrims.c','varPrims.c','boardHooks.c','boardHooks.h','version.h']
patch=[]
for name in files:
 old=(src/name).read_text(); new=old
 if name=='mem.c':new=new.replace('#if defined(NRF51)','#if defined(SMALLVM_UNOQ)\n\t#define OBJSTORE_BYTES 16384\n#elif defined(NRF51)',1)
 if name=='persist.c':
  new=new.replace('#elif defined(__ZEPHYR__)','#elif defined(__ZEPHYR__) && !defined(SMALLVM_UNOQ)')
  new=new.replace('#if defined(ESP8266)\n\t\t#define USE_CODE_FILE','#if defined(SMALLVM_UNOQ)\n\t\t#define HALF_SPACE (16 * 1024)\n\t#elif defined(ESP8266)\n\t\t#define USE_CODE_FILE')
 if name=='runtime.c':
  new=new.replace('#ifdef __ZEPHYR__','#if defined(__ZEPHYR__) && !defined(SMALLVM_UNOQ)')
  new=new.replace("delay(", "unoDelay(")
  new=fix(new)
  # Optional sets supplied as explicit no-op registrations by platform adapter.
 if name=='interp.c':
  new=new.replace('if (errorCode) goto error; \\', 'if (errorCode) goto error; \\\n\tif (!instructionBudget--) goto suspend; \\',1)
  new=new.replace('static void runTask(Task *task) {','static void runTask(Task *task) {\n\tunsigned instructionBudget = 256;',1)
  new=new.replace('void vmLoop() {','void vmSlice(unsigned cycles) {',1)
  a=new.index('void vmSlice('); b=new.index('#endif // not __EMSCRIPTEN__',a)
  piece=new[a:b].replace('int currentTaskIndex = 0;', 'static int currentTaskIndex = 0;').replace('int count = 0;', 'static int count = 0;').replace('while (true) {','while (cycles--) {',1)
  new=new[:a]+piece+'void vmLoop() { while (true) vmSlice(1); }\n\n'+new[b:]
 if name=='interp.h':new=new.replace('void vmLoop(void);','void vmLoop(void);\nvoid vmSlice(unsigned cycles);')
 (dst/name).write_text(new)
 patch.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/vm/'+name,tofile='b/vm/'+name))
(root/'firmware/adapter/smallvm.patch').write_text(''.join(patch))
for p in (root/'firmware/adapter').glob('*'):
 if p.suffix in ('.c','.cpp','.h'):shutil.copy2(p,dst.parent/p.name)
shutil.copy2(root/'firmware/adapter/smallvm_unoq.ino',dst.parents[1]/'smallvm_unoq.ino')
print('Prepared minimal SmallVM from canonical source, with explicit patch')
