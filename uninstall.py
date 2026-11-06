#!/usr/bin/env python3
"""Remove this package, retaining the original shell backup and unrelated files."""
import json
from pathlib import Path
import shutil
import subprocess
from install import UUID, START, END


def main():
    home = Path.home()
    app = home / '.local/share/whisper-dictation'
    state = app / 'install-state.json'
    if not state.exists() or json.loads(state.read_text()).get('project') != 'whisper-dictation-linux':
        raise SystemExit('No installation made by this package was found. Nothing was removed.')
    if json.loads(state.read_text()).get('shortcut'):
        subprocess.run(['gnome-extensions', 'disable', UUID], check=False)
        import gi
        gi.require_version('Gio', '2.0')
        from gi.repository import Gio
        settings = Gio.Settings.new('org.gnome.shell')
        settings.set_strv('enabled-extensions', [v for v in settings.get_strv('enabled-extensions') if v != UUID])
        settings.set_strv('disabled-extensions', [v for v in settings.get_strv('disabled-extensions') if v != UUID])
        Gio.Settings.sync()
        extension = home / '.local/share/gnome-shell/extensions' / UUID
        if extension.exists():
            shutil.rmtree(extension)
    bashrc = home / '.bashrc'
    if bashrc.exists():
        text = bashrc.read_text()
        start = text.find(START)
        end = text.find(END, start) if start >= 0 else -1
        if start >= 0 and end >= 0:
            bashrc.write_text(text[:start] + text[end + len(END):])
    for name in ('dictation.py', 'whisper-dictation', 'codex-dictation', 'shell.bash', 'ggml-base.en.bin', 'install-state.json'):
        (app / name).unlink(missing_ok=True)
    (home / '.local/share/applications/local.whisper.Dictation.desktop').unlink(missing_ok=True)
    print('Removed. Open a new terminal. Any original shell backup is still in', app)


if __name__ == '__main__':
    main()
