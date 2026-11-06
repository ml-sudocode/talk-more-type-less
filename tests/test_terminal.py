import ast
import os
from pathlib import Path
import pty
import re
import select
import signal
import sys
import tempfile
import time
import runpy
root = Path(__file__).resolve().parents[1] / 'app'
mod = runpy.run_path(str(root / 'codex-dictation'))
events = mod['InputEvents']()
assert events.feed(b'\x1b[103;') == []
assert events.feed(b'5u') == [('record', b'\x1b[103;5u')]
assert events.feed(b'\x1b[200~literal\x07\r\x1b[201~') == [('pass', b'\x1b[200~'), ('pass', b'literal\x07\r\x1b[201~')]
assert mod['paste_bytes']('hello\x1b\x03\r\nworld') == b'\x1b[200~hello\nworld\x1b[201~'
tree = ast.parse((root/'dictation.py').read_text())
f = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'apply_spoken_punctuation')
ns = {'re':re}
exec(compile(ast.Module(body=[f], type_ignores=[]), '<test>', 'exec'), ns)
assert ns['apply_spoken_punctuation']('Hello period Why question mark A right arrow B') == 'Hello. Why? A → B'
assert 'text = apply_spoken_punctuation(transcribe(audio))' in (root/'dictation.py').read_text()
print('PASS: terminal punctuation, enhanced keys, paste boundaries and control filtering', flush=True)
with tempfile.TemporaryDirectory() as folder:
    work = Path(folder)
    log = work/'input'
    heartbeat = work/'heartbeat'
    fake = work/'fake-codex'
    fake.write_text(f'''import os,select,tty,time
from pathlib import Path
tty.setraw(0)
while True:
    with open({str(heartbeat)!r}, 'ab') as f: f.write(b'.')
    if select.select([0], [], [], .03)[0]:
        data=os.read(0,4096)
        with open({str(log)!r},'ab') as f: f.write(data)
        if b'EXIT' in data: break
''')
    recorder = work/'fake-dictate'
    recorder.write_text('''#!/usr/bin/python3
import os,sys,tty,time
# Same noncanonical Enter behavior, with terminal-generated Ctrl+C.
import termios
s=termios.tcgetattr(0); s[3] &= ~(termios.ICANON | termios.ECHO); termios.tcsetattr(0, termios.TCSANOW,s)
while os.read(0,1) not in (b'\\r',b'\\n'): pass
time.sleep(.2)
print('Hello. Why?')
''')
    recorder.chmod(0o700)
    driver = work/'driver'
    driver.write_text(f'''import runpy,sys
m=runpy.run_path({str(root/'codex-dictation')!r})
m['main'].__globals__['DICTATE']={str(recorder)!r}
sys.argv=['wrapper','/usr/bin/python3',{str(fake)!r}]
sys.exit(m['main']())
''')
    pid, master = pty.fork()
    if pid == 0:
        os.execv('/usr/bin/python3', ['/usr/bin/python3',str(driver)])
    def pump(seconds):
        deadline=time.monotonic()+seconds
        while time.monotonic()<deadline:
            if select.select([master],[],[],.02)[0]:
                try: os.read(master,65536)
                except OSError: break
    def contents(): return log.read_bytes() if log.exists() else b''
    try:
        pump(.3)
        os.write(master,b'\x07')
        pump(.3)
        before=heartbeat.stat().st_size
        pump(.3)
        assert heartbeat.stat().st_size > before, 'Child must keep working while recording'
        assert contents() == b'', contents()
        os.write(master,b'\r')
        pump(.5)
        expected=b'\x1b[200~Hello. Why?\x1b[201~'
        assert contents() == expected, contents()
        os.write(master,b'\r')
        pump(.15)
        assert contents() == expected+b'\r', contents()
        os.write(master,b'\x07')
        pump(.2)
        os.write(master,b'\x03')
        pump(.3)
        assert contents() == expected+b'\r', contents()
        os.write(master,b'EXIT')
        pump(.2)
        done,status=os.waitpid(pid,os.WNOHANG)
        assert done == pid and os.waitstatus_to_exitcode(status) == 0, (done,status)
        print('PASS: child keeps working; recording sends no interrupt; paste stays unsent until separate Enter; cancel preserves draft; clean exit')
    finally:
        try: os.kill(pid,signal.SIGTERM)
        except ProcessLookupError: pass
        os.close(master)
