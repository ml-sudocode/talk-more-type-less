#!/usr/bin/python3
"""Small GTK interface. Audio and working files live only in sandbox /tmp."""
import errno
import re
import fcntl
import argparse
from contextlib import contextmanager
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import termios
import wave

# GTK may consume these environment variables during initialization.
ACTIVATION_TOKEN = os.environ.get('XDG_ACTIVATION_TOKEN') or os.environ.get('DESKTOP_STARTUP_ID', '')

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk, GLib, Gtk

os.umask(0o077)
GLib.set_prgname('local.whisper.Dictation')
MODEL = '/app/ggml-base.en.bin'

def recorder_command(audio):
    return ['pw-record', '--rate=16000', '--channels=1', '--format=s16',
            '--properties={ media.name = "Whisper Dictation" }', str(audio)]

def recorder_error(log):
    log.seek(0)
    lines = log.read().decode('utf-8', errors='replace').strip().splitlines()
    details = [line for line in lines if line and not line.startswith('/tmp/')]
    return 'Microphone recording failed. ' + (' '.join(details[-3:])[:500] or 'The recorder stopped unexpectedly.')

def stop_and_validate(recorder, audio, error_log):
    # pw-record 1.6.2 on this Ubuntu release returns 1 on normal SIGINT.
    # Accept it only when we requested Stop, and independently validate the WAV.
    requested_stop = recorder.poll() is None
    if requested_stop:
        recorder.send_signal(signal.SIGINT)
    try:
        recorder.wait(timeout=5)
    except subprocess.TimeoutExpired:
        recorder.kill()
        recorder.wait()
        raise RuntimeError('The microphone recorder did not stop in time.')
    if not requested_stop or recorder.returncode not in (0, 1, -signal.SIGINT):
        raise RuntimeError(recorder_error(error_log))
    try:
        with wave.open(str(audio), 'rb') as recording:
            if (recording.getframerate(), recording.getnchannels(), recording.getsampwidth()) != (16000, 1, 2):
                raise RuntimeError('The microphone returned an unsupported audio format.')
            frames = recording.getnframes()
            if frames < 2000:
                raise RuntimeError('The recording was too short. Please speak for a few seconds.')
            if len(recording.readframes(frames)) != frames * 2:
                raise RuntimeError('The microphone recording was incomplete. Please try again.')
    except (OSError, EOFError, wave.Error) as exc:
        raise RuntimeError('The recorder did not produce a valid audio file. ' + recorder_error(error_log)) from exc

@contextmanager
def terminal_keys():
    if not sys.stdin.isatty():
        yield
        return
    fd = sys.stdin.fileno()
    original = termios.tcgetattr(fd)
    keys = original[:]
    keys[6] = original[6][:]
    keys[0] &= ~(termios.IGNCR | termios.ICRNL | termios.INLCR)
    keys[3] &= ~(termios.ICANON | termios.ECHO | termios.ECHONL)
    keys[3] |= termios.ISIG
    keys[6][termios.VMIN] = 1
    keys[6][termios.VTIME] = 0
    try:
        termios.tcsetattr(fd, termios.TCSANOW, keys)
        yield
    finally:
        termios.tcsetattr(fd, termios.TCSANOW, original)

def wait_for_enter(recorder=None, log=None, timeout=None):
    import select
    deadline = time.monotonic() + timeout if timeout else None
    while deadline is None or time.monotonic() < deadline:
        if recorder is not None and recorder.poll() is not None:
            raise RuntimeError(recorder_error(log))
        if select.select([sys.stdin.fileno()], [], [], 0.1)[0]:
            key = os.read(sys.stdin.fileno(), 1)
            if not key:
                raise RuntimeError('Recording cancelled: terminal input closed.')
            if key in (b'\r', b'\n'):
                return
            if key == b'\x03':
                raise KeyboardInterrupt

def terminal_dictation(seconds=None, start_immediately=False):
    with terminal_keys():
        _terminal_dictation(seconds, start_immediately)

def _terminal_dictation(seconds=None, start_immediately=False):
    if seconds is None and not sys.stdin.isatty():
        raise RuntimeError('Use an interactive terminal, or specify --seconds 10.')
    recorder = None
    with tempfile.TemporaryDirectory(prefix='dictation-') as folder, tempfile.TemporaryFile() as log:
        audio = Path(folder) / 'speech.wav'
        try:
            if seconds is None and not start_immediately:
                print('Press Enter to start recording; press Enter again to stop.', file=sys.stderr, flush=True)
                wait_for_enter()
            recorder = subprocess.Popen(recorder_command(audio), stdout=subprocess.DEVNULL, stderr=log)
            print('Recording…' + (f' ({seconds:g} seconds)' if seconds else ' Press Enter to stop.'), file=sys.stderr, flush=True)
            if seconds is None:
                wait_for_enter(recorder, log, timeout=120)
            else:
                try:
                    recorder.wait(timeout=seconds)
                except subprocess.TimeoutExpired:
                    pass
            stop_and_validate(recorder, audio, log)
            print('Transcribing…', file=sys.stderr, flush=True)
            text = apply_spoken_punctuation(transcribe(audio))
            if text:
                print(text, flush=True)
            else:
                raise RuntimeError('No speech recognized. Please try again.')
        finally:
            if recorder is not None and recorder.poll() is None:
                recorder.kill()
                recorder.wait()

def apply_spoken_punctuation(text):
    """Explicit spoken commands override adjacent punctuation guessed by Whisper."""
    commands = {
        'period': '.', 'full stop': '.', 'comma': ',',
        'question mark': '?', 'exclamation mark': '!', 'exclamation point': '!',
        'colon': ':', 'semicolon': ';', 'semi colon': ';',
        'new line': '\n', 'new paragraph': '\n\n',
        'slash': '/', 'right arrow': '→', 'left arrow': '←',
        'open quote': '“', 'close quote': '”', 'dash': '—',
    }
    phrases = '|'.join(re.escape(word).replace(r'\ ', r'\s+') for word in commands)
    pattern = r'[ \t]*[.,;:!?]*[ \t]*\b(' + phrases + r')\b[.,;:!?]*[ \t]*'
    def replace(match):
        command = ' '.join(match.group(1).lower().split())
        mark = commands[command]
        if mark in ('→', '←', '—'):
            return ' ' + mark + ' '
        if mark == '“':
            return ' “'
        if mark == '/':
            return '/'
        return mark if mark.startswith('\n') else mark + ' '
    text = re.sub(pattern, replace, text, flags=re.IGNORECASE)
    text = re.sub(r'[ \t]+([.,;:!?])', r'\1', text)
    text = re.sub(r'[ \t]*\n[ \t]*', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'“[ \t]+', '“', text)
    text = re.sub(r'[ \t]+”', '”', text)
    return text.strip()

def transcribe(audio):
    result = subprocess.run(
        ['whisper-cli', '-m', MODEL, '-f', str(audio), '-l', 'en',
         '-t', '4', '-ng', '-nt', '-np'],
        capture_output=True, text=True, timeout=300,
    )
    if result.returncode:
        raise RuntimeError('Whisper could not transcribe this recording.')
    return ' '.join(result.stdout.split())

class WindowInstance:
    """Serialize GUI starts and forward activation to the existing window."""
    def __init__(self):
        folder = Path(os.environ['XDG_RUNTIME_DIR']) / 'whisper-dictation'
        self.lock = (folder / 'window.lock').open('a')
        self.path = folder / 'window.sock'
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

    def acquire(self):
        deadline = time.monotonic() + 5
        while True:
            try:
                fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                try:
                    self.socket.sendto(b'present\0' + ACTIVATION_TOKEN.encode('utf-8'), str(self.path))
                    return False
                except (FileNotFoundError, ConnectionRefusedError):
                    if time.monotonic() >= deadline:
                        raise RuntimeError('The existing dictation window is not responding.')
                    time.sleep(0.05)
            else:
                self.path.unlink(missing_ok=True)
                self.socket.bind(str(self.path))
                self.socket.setblocking(False)
                return True

    def watch(self, window):
        def activate(_fd, _condition):
            try:
                message = self.socket.recv(16384)
            except BlockingIOError:
                return True
            command, _, token = message.partition(b'\0')
            if command == b'present':
                window.deiconify()
                if token:
                    # Activates the mapped Wayland surface with this launch's token.
                    window.set_startup_id(token.decode('utf-8', errors='replace'))
                else:
                    window.present()
            return True
        GLib.io_add_watch(self.socket.fileno(), GLib.IO_IN, activate)

class Dictation(Gtk.Window):
    def __init__(self):
        super().__init__(title='Whisper Dictation')
        self.set_default_size(610, 400)
        self.set_border_width(20)
        self.connect('delete-event', self.close)
        self.recorder = None
        self.busy = False
        self.closed = False
        self.recording_started = None
        self.temp = tempfile.TemporaryDirectory(prefix='dictation-')
        self.audio = Path(self.temp.name) / 'speech.wav'
        self.error_log = None
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.add(box)
        heading = Gtk.Label(label='Speak, transcribe, and copy')
        heading.set_xalign(0)
        box.pack_start(heading, False, False, 0)
        self.status = Gtk.Label(label='Ready. Click Clear text and record when you want to speak.')
        self.status.set_xalign(0)
        self.status.set_line_wrap(True)
        box.pack_start(self.status, False, False, 0)
        controls = Gtk.Box(spacing=10)
        self.record_button = Gtk.Button(label='Clear text and record')
        self.record_button.connect('clicked', self.toggle)
        controls.pack_start(self.record_button, False, False, 0)
        self.copy_button = Gtk.Button(label='Copy text')
        self.copy_button.set_sensitive(False)
        self.copy_button.connect('clicked', self.copy_text)
        controls.pack_start(self.copy_button, False, False, 0)
        clear = Gtk.Button(label='Clear')
        clear.connect('clicked', self.clear)
        controls.pack_end(clear, False, False, 0)
        box.pack_start(controls, False, False, 0)
        self.spoken_punctuation = Gtk.CheckButton(label='Spoken punctuation (period, comma, question mark)')
        self.spoken_punctuation.set_active(True)
        box.pack_start(self.spoken_punctuation, False, False, 0)
        self.view = Gtk.TextView()
        self.view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.view.set_left_margin(10)
        self.view.set_right_margin(10)
        self.view.set_top_margin(10)
        self.view.get_buffer().connect('changed', self.text_changed)
        scroll = Gtk.ScrolledWindow()
        scroll.set_shadow_type(Gtk.ShadowType.IN)
        scroll.add(self.view)
        box.pack_start(scroll, True, True, 0)
        foot = Gtk.Label(label='English · No saved history\nKeep this window open while pasting copied text.')
        foot.set_xalign(0)
        box.pack_end(foot, False, False, 0)
        GLib.timeout_add(250, self.tick)

    def text_changed(self, buffer):
        self.copy_button.set_sensitive(buffer.get_char_count() > 0)

    def clear(self, _button):
        self.view.get_buffer().set_text('')
        Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).clear()

    def copy_text(self, _button):
        buffer = self.view.get_buffer()
        text = buffer.get_text(*buffer.get_bounds(), False)
        Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).set_text(text, -1)
        self.status.set_text('Copied. Paste with Ctrl+V, or Ctrl+Shift+V in Terminal.')

    def toggle(self, _button):
        if self.busy:
            return
        if self.recorder is not None:
            self.stop_recording()
            return
        try:
            self.audio.unlink(missing_ok=True)
            self.error_log = tempfile.TemporaryFile()
            self.recorder = subprocess.Popen(
                recorder_command(self.audio),
                stdout=subprocess.DEVNULL, stderr=self.error_log,
            )
            self.view.get_buffer().set_text('')
            self.recording_started = time.monotonic()
            self.record_button.set_label('Stop and transcribe')
            self.status.set_text('Recording… Click Stop and transcribe when finished.')
        except OSError:
            self.finish('Could not start the microphone recorder.', error=True)

    def tick(self):
        if self.closed:
            return False
        if self.recorder is not None and not self.busy:
            if self.recorder.poll() is not None:
                self.finish(recorder_error(self.error_log), error=True)
            elif time.monotonic() - self.recording_started >= 120:
                self.stop_recording()
        return True

    def stop_recording(self):
        self.busy = True
        self.record_button.set_sensitive(False)
        self.status.set_text('Transcribing…')
        threading.Thread(target=self.process_recording, daemon=True).start()

    def process_recording(self):
        try:
            stop_and_validate(self.recorder, self.audio, self.error_log)
            text = transcribe(self.audio)
            GLib.idle_add(self.finish, text or 'No speech recognized. Please try again.', not bool(text))
        except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
            message = str(exc) if isinstance(exc, RuntimeError) else 'Recording or transcription failed. Please try again.'
            GLib.idle_add(self.finish, message, True)
        finally:
            self.audio.unlink(missing_ok=True)

    def finish(self, text, error=False):
        if self.closed:
            return False
        if self.recorder is not None and self.recorder.poll() is None:
            self.recorder.kill()
            self.recorder.wait()
        self.recorder = None
        if self.error_log:
            self.error_log.close()
            self.error_log = None
        self.audio.unlink(missing_ok=True)
        self.busy = False
        self.record_button.set_label('Clear text and record')
        self.record_button.set_sensitive(True)
        if error:
            self.status.set_text(text)
        else:
            if self.spoken_punctuation.get_active():
                text = apply_spoken_punctuation(text)
            self.view.get_buffer().set_text(text)
            self.status.set_text('Ready. Review the text, then click Copy text.')
        return False

    def close(self, *_args):
        self.closed = True
        if self.recorder is not None and self.recorder.poll() is None:
            self.recorder.kill()
            self.recorder.wait()
        self.temp.cleanup()
        Gtk.main_quit()
        return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Local English dictation; records only when started. Prints text without executing it.')
    parser.add_argument('--terminal', action='store_true', help='Record and print text in the terminal')
    parser.add_argument('--start', action='store_true', help='Start recording immediately in terminal mode; Enter stops')
    parser.add_argument('--seconds', type=float, help='Record for 0.5–120 seconds in terminal mode')
    parser.add_argument('--self-test', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--ui-check', action='store_true', help=argparse.SUPPRESS)
    options = parser.parse_args()
    if options.seconds is not None and (not options.terminal or not 0.5 <= options.seconds <= 120):
        parser.error('--seconds requires --terminal and a value from 0.5 to 120')
    if options.start and not options.terminal:
        parser.error('--start requires --terminal')
    if options.terminal:
        try:
            terminal_dictation(options.seconds, options.start)
        except (KeyboardInterrupt, EOFError):
            print('\nCancelled.', file=sys.stderr)
            sys.exit(130)
        except (RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
            print(f'Error: {exc}', file=sys.stderr)
            sys.exit(1)
    elif options.self_test:
        with socket.socket() as sock:
            sock.settimeout(2)
            try:
                sock.connect(('1.1.1.1', 443))
            except OSError as exc:
                assert exc.errno == errno.ENETUNREACH, exc
                print('PASS: direct network access blocked')
            else:
                raise RuntimeError('Network isolation failed')
        assert not Path('/home').exists()
        print('PASS: personal files not exposed')
        assert Gtk.init_check()[0], 'Wayland connection failed'
        result = subprocess.run(['pw-cli', 'info', '0'], capture_output=True, timeout=5)
        assert result.returncode == 0, 'PipeWire connection failed'
        print('PASS: desktop and audio service accessible; microphone not recorded')
        start = time.monotonic()
        text = transcribe('/usr/share/sounds/debian/samples/en-Wikipedia-Ignore_All_Rules.wav')
        assert len(text) > 100, text
        print(f'PASS: bundled sample transcribed in {time.monotonic()-start:.1f}s')
        print(text)
    elif options.ui_check:
        window = Dictation()
        window.show_all()
        def check_window():
            assert window.get_visible()
            assert window.recorder is None
            print('PASS: dictation window opens with microphone off')
            window.destroy()
            Gtk.main_quit()
            return False
        GLib.timeout_add(300, check_window)
        Gtk.main()
    else:
        instance = WindowInstance()
        if instance.acquire():
            window = Dictation()
            instance.watch(window)
            window.show_all()
            Gtk.main()
