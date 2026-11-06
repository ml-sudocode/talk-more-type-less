# Talk More, Type Less

**Dictate into your coding agent or your documents, with speech recognition running on your own computer.**

I built this to solve two problems:

- **Talking to my agent in the terminal.** I wanted to dictate my next instruction while the agent kept working, review the transcript, and send it when ready.
- **Dictating into documents without uploading my audio.** For a while, I used ChatGPT’s dictation feature and copied the text elsewhere. I wanted local transcription with network access blocked for the recording and transcription process.

I use a **Mac running Ubuntu Linux in an ARM64 virtual machine**. That’s where I built and use this setup.

Talk More, Type Less uses [Whisper through whisper.cpp](https://github.com/ggml-org/whisper.cpp) for English speech recognition. It provides two workflows:

| Where you’re working | How to dictate |
|---|---|
| Bash or Codex in the terminal | Press **Ctrl+G** to record and insert an editable draft. |
| Documents and other apps | Press **Ctrl+Shift+G** to open a recording window, then copy and paste the transcript. |

## Kinks that I ironed out (for impatient people)

Getting Whisper to recognize speech was only part of the job. These details made it useful in my daily work:

- **Keep the agent working.** Starting terminal dictation doesn’t open an external editor or send an interrupt to Codex.
- **Separate recording from sending.** Enter stops recording. A separate Enter sends the reviewed draft.
- **Speak in bursts.** Each recording adds to the current draft, so I can pause, think, and continue without sending an unfinished message.
- **Reach dictation from other apps.** A GNOME shortcut opens the recording window without switching to the terminal.
- **Start a fresh segment with one click.** **Clear text and record** replaces selecting and deleting the previous transcript.
- **Specify punctuation.** I’ve spent years dictating into text boxes, so saying “comma,” “period,” and “question mark” comes naturally. Models often guess punctuation differently from what I intended. This setup converts spoken commands into punctuation in both workflows.

## Other dictation tools

[Handy](https://github.com/cjpais/Handy), [Speech Note](https://github.com/mkiol/dsnote), and [Myna](https://github.com/canonical/myna) also offer local dictation. They may work well with coding agents; I haven’t compared them in that workflow.

Canonical released Myna’s public technology preview only on **12 October 2026**. Its announcement lists Intel/AMD architectures. I haven’t investigated whether it runs in my ARM64 virtual machine. [Canonical’s announcement](https://ubuntu.com/blog/myna-speech-to-text-technology-preview-available)

## Set it up

These instructions target **Ubuntu 26.04 with GNOME 50, Wayland, PipeWire, and Bash**. This is an early release, not a native macOS or Windows app.

You need an internet connection for setup and the first speech-model download. Transcription then works offline.

1. Choose **Code → Download ZIP** on this GitHub page and extract the folder.
2. Right-click inside the extracted folder and choose **Open in Terminal**.
3. Install the supporting software:

   ```sh
   sudo apt update
   sudo apt install whisper.cpp pipewire-bin bubblewrap python3-gi gir1.2-gtk-3.0 libglib2.0-bin gnome-shell-extension-prefs
   ```

4. Run setup **without sudo**:

   ```sh
   /usr/bin/python3 install.py
   ```

   Setup downloads and checks an English speech model of about 148 MB. It installs the tools for your account and adds the terminal shortcuts to your Bash startup file, keeping a backup.

5. **Sign out of Ubuntu and sign back in** to activate Ctrl+Shift+G.
6. Press **Ctrl+Shift+G** to open the dictation window. Click **Clear text and record**, speak, then click **Stop and transcribe**. Review the text and use **Copy text** to paste it into another app.
7. Open a new Bash terminal. Start or resume Codex from that terminal to use Ctrl+G there.

You can also open **Talk More, Type Less** from the applications menu. Codex must be installed separately.

If setup detects an existing custom installation, it stops rather than replacing it. Back up and move that installation aside before proceeding.

### Other Linux desktops

The global shortcut supports **GNOME 50 only**. Other desktop combinations have not been tested.

To install without the GNOME shortcut:

```sh
/usr/bin/python3 install.py --no-shortcut
```

Open the recording window from the applications menu.

### Use an existing speech model

If you already have the supported `ggml-base.en.bin` file:

```sh
/usr/bin/python3 install.py --model /path/to/ggml-base.en.bin
```

Setup checks that the file matches the expected version. The model is distributed separately by [whisper.cpp](https://github.com/ggml-org/whisper.cpp/tree/master/models).

## Everyday use

### For documents and other apps

1. Press **Ctrl+Shift+G**.
2. Click **Clear text and record**, then speak.
3. Click **Stop and transcribe**.
4. Review and edit the result.
5. Click **Copy text**, switch to your app, and paste.

Most apps use **Ctrl+V** to paste; Ubuntu Terminal usually uses **Ctrl+Shift+V**. Keep the dictation window open until you’ve pasted.

### In Bash or Codex

1. Press **Ctrl+G** and speak.
2. Press **Enter** to stop recording and wait for the transcript.
3. To add more, press **Ctrl+G** again. The existing draft stays in place, and the next transcription is inserted at the cursor.
4. Repeat as needed, then review the complete message.
5. Press **Enter outside a recording** to send the message—or run the command at a Bash prompt.

You can build a message in short bursts. Stopping a recording does not submit it.

**Ctrl+C cancels a recording.** Other typing is ignored while recording or waiting for transcription.

The terminal shortcut works at the Bash prompt and in Codex sessions started through this integration. It does not add dictation to every terminal program. Existing sessions need to be restarted to pick up changes.

Review dictated shell commands carefully before running them.

## Mic setup

I had to fiddle with the sound options on the VM controls: select "virtio-sound-device"; and USB Devices > connect to the mic. I believe these are VM-specific configs, so you may have to do some trial and error. 

For either setup, inside your Linux VM, select the microphone under **Ubuntu Settings → Sound → Input** and check that the mic is not on mute (Ubuntu seems to default to putting the mic on Mute on startup). 

### Recommended: a wired lavalier and USB sound card

Connect a **battery-free wired lavalier** to a **USB sound card**. 

A lavalier mic is a tiny microphone. I leave it on my desk and it picks up sound fine; alternatively you can pin it to your shirt. 

This setup needs no charging, so you can leave it on 24/7, and takes up almost no desk space!

Note: Usually you will need a USB sound card; plugging the lavalier mic into the headphone jack generally does not work.

- Wired lavalier microphone: [Example](https://www.amazon.com/Neewer-Microphone-Compatible-Omnidirectional-Condenser/dp/B0CV196ZCZ)
- USB sound card: [Example](https://www.amazon.com/VENTION-External-Control-Adapter-Windows/dp/B0CYSX4QMJ)

### Prefer wireless?

Consider a clip-on microphone with a **transmitter you wear** and a **receiver that plugs into the computer**. Downside is that you have to charge the mic; you could buy two transmitters and alternate them.

Examples: [Option 1](https://www.amazon.com/BOYA-Wireless-Microphone-Reduction-Recording/dp/B0DJSM8PHP/), [Option 2](https://www.amazon.com/)

## Spoken punctuation

| Say | Get |
|---|---|
| period / full stop | . |
| comma | , |
| question mark | ? |
| exclamation mark / exclamation point | ! |
| colon | : |
| semicolon / semi colon | ; |
| slash | / |
| right arrow | → |
| left arrow | ← |
| open quote | “ |
| close quote | ” |
| dash | — |
| new line | A line break |
| new paragraph | A blank line |

**“Hello comma how are you question mark”** becomes **“Hello, how are you?”**

These conversions happen locally after transcription, without another AI service. Whisper may still guess punctuation elsewhere.

Uncheck **Spoken punctuation** in the window when you want the command words written literally. Terminal dictation always converts them. The conversion does not correct spelling or capitalization.

## Privacy

Recording and transcription run with direct network access blocked and limited file access. Temporary audio is removed after use, and the tool keeps no transcript history.

Recording starts only when you click the record button or press Ctrl+G.

Clipboard contents, terminal history, and submitted text follow the behavior of the receiving app. **Sending a dictated prompt to Codex sends the text to Codex**, just as typing it would.

## Troubleshooting

- **No microphone sound:** check the selected input and meter in Ubuntu’s Sound settings.
- **Ctrl+Shift+G does nothing:** sign out and back in. In the Extensions app, check that **Talk More, Type Less Shortcut** is enabled. It requires GNOME 50.
- **Another app uses the shortcut:** remove the conflicting assignment in Ubuntu’s Keyboard settings.
- **Ctrl+G opens an editor or pauses Codex:** start Codex from a new Bash terminal.
- **Punctuation commands appear as words:** enable **Spoken punctuation** in the window. Reopen windows left running from before an update.
- **Recording fails:** try speaking for more than a second. Recordings stop automatically after two minutes.
- **Transcription is slow:** speed depends on your computer. This setup uses the English `base.en` model on the CPU.
- **A supporting package is unavailable:** the installation instructions target Ubuntu 26.04; other releases may have different packages.

When reporting a problem, include your Ubuntu and desktop versions, the shortcut you used, and what happened. Leave out private recordings and login information.

## Remove it

From the downloaded project folder, run:

```sh
/usr/bin/python3 uninstall.py
```

Open a new terminal afterward. The original Bash backup is kept. Close existing dictation windows and Codex sessions when convenient.

## Project status and contributions

Recording and transcription have been used in an ARM64 Ubuntu environment. Automated tests cover punctuation, cancellation, draft insertion, and keeping a simulated task running during dictation.

Bug reports, compatibility reports, and clearer instructions are welcome. See [Contributing](CONTRIBUTING.md) and [Testing](tests/README.md).

## Thanks and license

Built with [whisper.cpp](https://github.com/ggml-org/whisper.cpp), [OpenAI Whisper](https://github.com/openai/whisper), GTK, PipeWire, Bubblewrap, and GNOME.

This project uses the [MIT License](LICENSE). Supporting software and the separately downloaded model retain their own licenses. This is not an official OpenAI or Insta360 product.
