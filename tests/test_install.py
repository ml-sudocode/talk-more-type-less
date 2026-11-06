import importlib.util
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('installer', ROOT / 'install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)
with tempfile.TemporaryDirectory() as folder:
    home = Path(folder) / 'a home with spaces'
    home.mkdir()
    bashrc = home / '.bashrc'
    bashrc.write_text('# original setting\n')
    model = Path(folder) / 'model'
    model.write_bytes(b'test model; no network needed')
    app = installer.install_files(home, model, False)
    assert (app / 'ggml-base.en.bin').read_bytes() == model.read_bytes()
    assert (app / 'bashrc-before-install').read_text() == '# original setting\n'
    assert bashrc.read_text().count(installer.START) == 1
    installer.install_files(home, model, False)
    assert bashrc.read_text().count(installer.START) == 1
    assert 'Exec="' in (home / '.local/share/applications/io.github.sandstonelabs.TalkMoreTypeLess.desktop').read_text()
    assert (app / 'talk-more-type-less').stat().st_mode & 0o111
    try:
        installer.verify_model(model)
    except RuntimeError:
        pass
    else:
        raise AssertionError('Incorrect model must be rejected')
    other = Path(folder) / 'existing user'
    existing = other / '.local/share/talk-more-type-less'
    existing.mkdir(parents=True)
    (existing / 'keep').write_text('my custom setup')
    try:
        installer.install_files(other, model, False)
    except RuntimeError:
        pass
    else:
        raise AssertionError('Custom setup must not be overwritten')
    assert (existing / 'keep').read_text() == 'my custom setup'
print('PASS: installation with spaces, repeat installation, backup, model validation and custom setup protection')
