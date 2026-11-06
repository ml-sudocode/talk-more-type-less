#!/usr/bin/env python3
"""Install this project for the current user; never run with sudo."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parent
MODEL_URL = 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin'
MODEL_HASH = 'a03779c86df3323075f5e796cb2ce5029f00ec8869eee3fdfb897afe36c6d002'
UUID = 'talk-more-type-less-shortcut@local'
START = '# >>> Talk More, Type Less >>>'
END = '# <<< Talk More, Type Less <<<'


def verify_model(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    if digest.hexdigest() != MODEL_HASH:
        raise RuntimeError('The speech model did not pass its download check. Please download it again.')


def preflight():
    missing = [name for name in ('bwrap', 'pw-record', 'whisper-cli', 'glib-compile-schemas') if not shutil.which(name)]
    check = subprocess.run(['/usr/bin/python3', '-c', "import gi; gi.require_version('Gtk', '3.0'); gi.require_version('Gdk', '3.0'); from gi.repository import Gtk, Gdk"], capture_output=True)
    if check.returncode:
        missing.append('Python GTK 3 support')
    if missing:
        raise RuntimeError('Please install the supporting software listed in the README first. Missing: ' + ', '.join(missing))
    if not Path('/usr/bin/whisper-cli').exists():
        raise RuntimeError('This package expects the Ubuntu whisper.cpp package at /usr/bin/whisper-cli.')


def desktop_quote(path):
    return '"' + str(path).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace('%', '%%') + '"'


def install_files(home, model, shortcut):
    app = home / '.local/share/talk-more-type-less'
    if app.exists() and not (app / 'install-state.json').exists():
        raise RuntimeError('A different dictation setup already exists. Nothing was replaced. Back it up and move it aside before installing this package.')
    if app.exists() and json.loads((app / 'install-state.json').read_text()).get('project') != 'talk-more-type-less':
        raise RuntimeError('This folder belongs to a different installation. Nothing was changed.')
    extension = home / '.local/share/gnome-shell/extensions' / UUID
    if shortcut and extension.exists() and not (app / 'install-state.json').exists():
        raise RuntimeError('A shortcut extension already exists; review it before replacing it.')
    app.mkdir(parents=True, exist_ok=True)
    for name in ('dictation.py', 'talk-more-type-less', 'codex-dictation', 'shell.bash'):
        shutil.copy2(ROOT / 'app' / name, app / name)
    for name in ('talk-more-type-less', 'codex-dictation'):
        (app / name).chmod(0o755)
    destination = app / 'ggml-base.en.bin'
    if model.resolve() != destination.resolve():
        shutil.copyfile(model, destination)
    desktop = home / '.local/share/applications/io.github.sandstonelabs.TalkMoreTypeLess.desktop'
    desktop.parent.mkdir(parents=True, exist_ok=True)
    desktop.write_text('[Desktop Entry]\nType=Application\nName=Talk More, Type Less\nComment=Speak and turn your words into text locally\nExec=' + desktop_quote(app / 'talk-more-type-less') + '\nIcon=audio-input-microphone\nTerminal=false\nCategories=AudioVideo;Audio;\nStartupNotify=true\n')
    bashrc = home / '.bashrc'
    content = bashrc.read_text() if bashrc.exists() else ''
    if START not in content:
        if bashrc.exists() and not (app / 'bashrc-before-install').exists():
            shutil.copy2(bashrc, app / 'bashrc-before-install')
        content += '\n' + START + '\nsource ' + shlex.quote(str(app / 'shell.bash')) + '\n' + END + '\n'
        bashrc.write_text(content)
    if shortcut:
        shutil.copytree(ROOT / 'gnome-extension', extension, dirs_exist_ok=True)
        subprocess.run(['glib-compile-schemas', '--strict', str(extension / 'schemas')], check=True)
    old_state = json.loads((app / 'install-state.json').read_text()) if (app / 'install-state.json').exists() else {}
    (app / 'install-state.json').write_text(json.dumps({'project': 'talk-more-type-less', 'shortcut': shortcut or old_state.get('shortcut', False)}, indent=2) + '\n')
    return app


def enable_shortcut():
    import gi
    gi.require_version('Gio', '2.0')
    from gi.repository import Gio
    settings = Gio.Settings.new('org.gnome.shell')
    enabled = settings.get_strv('enabled-extensions')
    settings.set_strv('enabled-extensions', list(dict.fromkeys(enabled + [UUID])))
    disabled = settings.get_strv('disabled-extensions')
    settings.set_strv('disabled-extensions', [item for item in disabled if item != UUID])
    Gio.Settings.sync()


def main():
    parser = argparse.ArgumentParser(description='Set up Talk More, Type Less for your Linux account.')
    parser.add_argument('--model', type=Path, help='Use an already downloaded ggml-base.en.bin')
    parser.add_argument('--no-shortcut', action='store_true', help='Skip the GNOME 50 global shortcut')
    parser.add_argument('--check', action='store_true', help='Check supporting software without changing anything')
    args = parser.parse_args()
    if os.geteuid() == 0:
        parser.error('Run this as your normal user, without sudo.')
    preflight()
    shortcut = not args.no_shortcut
    if shortcut:
        version = subprocess.run(['gnome-shell', '--version'], capture_output=True, text=True) if shutil.which('gnome-shell') else None
        if version is None or not version.stdout.startswith('GNOME Shell 50.'):
            raise RuntimeError('The global shortcut currently supports GNOME 50. Use --no-shortcut to install the window and terminal tools without it.')
    if args.check:
        print('Supporting software found. No files or settings were changed.')
        return
    app = Path.home() / '.local/share/talk-more-type-less'
    if app.exists() and not (app / 'install-state.json').exists():
        raise RuntimeError('An existing custom dictation setup was found. Nothing was changed. See the README before replacing it.')
    with tempfile.TemporaryDirectory(prefix='whisper-setup-') as temporary:
        model = args.model or (app / 'ggml-base.en.bin')
        if not model.exists() and args.model is None:
            model = Path(temporary) / 'ggml-base.en.bin'
            print('Downloading the English speech model (about 148 MB). This is needed only once.', flush=True)
            urllib.request.urlretrieve(MODEL_URL, model)
        verify_model(model)
        install_files(Path.home(), model, shortcut)
    if shortcut:
        enable_shortcut()
    print('Installed. Open a new Bash terminal for Ctrl+G.')
    if shortcut:
        print('Sign out and sign back in once to activate Ctrl+Shift+G everywhere.')
    print('You can also open Talk More, Type Less from your applications menu.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        raise SystemExit(str(error))
