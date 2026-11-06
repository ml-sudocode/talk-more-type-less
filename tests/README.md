# Checks for contributors

These checks use simulated input. They do not open your microphone or call an AI service.

From the project folder, run:

```sh
python3 tests/test_punctuation.py
python3 tests/test_terminal.py
python3 tests/test_install.py
node tests/test_shortcut.cjs
bash -n app/shell.bash
glib-compile-schemas --strict --dry-run gnome-extension/schemas
```

The terminal check uses a pretend Codex process that keeps doing work while a pretend recording runs. It checks that recording does not send an interrupt, that the transcript arrives as an unsent paste, and that a separate Enter is needed to submit it.

The installer check uses a temporary home folder and a small fake model file. It does not download a model or change your desktop settings. The shortcut check uses simulated GNOME windows; it cannot prove real desktop focus behavior.

Before calling a release fully tested, also try a fresh Ubuntu installation, a real microphone, Ctrl+Shift+G while another app is active, and Ctrl+G while Codex is working. Test cancelling a recording and removing the installation too.
