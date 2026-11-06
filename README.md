# Talk More, Type Less

Speak instead of typing. Turn your speech into text on your own computer, then review it before you send it anywhere.

This small project gives you a dictation window, spoken punctuation, and a way to dictate into Bash and Codex. It uses [Whisper through whisper.cpp](https://github.com/ggml-org/whisper.cpp) to recognize English speech locally. No transcription subscription or online speech service is needed.

**Current home:** Ubuntu 26.04, GNOME 50, Wayland, PipeWire, and Bash. This is an early release made from a personal setup. The global shortcut and live Codex behavior still need wider testing. It is not a Windows or macOS installer.

## What you can do

- **Press Ctrl+Shift+G from any app** to open the dictation window or return to the one already open. The GNOME shortcut needs a sign-out and sign-in after setup.
- Click **Clear text and record** to start a fresh segment without selecting and deleting the old text.
- Say punctuation out loud: “comma,” “question mark,” “new paragraph,” and more.
- **Press Ctrl+G in a Bash terminal or a Codex session started from that terminal** to dictate into your draft.
- Keep Codex working while you dictate. The terminal helper inserts text without sending it or pressing an interrupt key.

The desktop window does not type directly into other apps. Review the result, click **Copy text**, and paste it where you want it.

## A small microphone setup that stays out of the way

### Recommended: a wired lavalier microphone and a USB sound card

A lavalier is a tiny microphone that clips to your shirt. Connect a **battery-free wired lavalier microphone** to a small **USB sound card with a microphone input**, then plug that into your computer.

Why this is a convenient desk setup:

- **Nothing needs charging.** The USB adapter supplies the microphone power, provided you choose a compatible, battery-free microphone.
- **It is tiny.** There is no large microphone or stand taking up desk space.
- **The microphone stays close to your mouth** while you move naturally in your chair.

Check that the microphone plug matches the sound card's microphone socket. Some phone-style microphones need an adapter. A USB adapter with only a headphone output will not work.

**Amazon link placeholders — replace these when you choose your products:**

- Wired lavalier microphone: **[ADD AMAZON LINK HERE]**
- USB sound card with a microphone input: **[ADD AMAZON LINK HERE]**
- Optional plug adapter, if needed: **[ADD AMAZON LINK HERE]**

### Prefer wireless?

Look for a small clip-on wireless microphone with a **transmitter** that you wear and a **receiver** that plugs into the computer. A kit such as an **Insta360 Mic Air with its USB-C receiver**, or a similar transmitter-and-receiver kit, is the kind of setup to consider.

Make sure the kit includes the receiver: some listings sell only the transmitter. Check computer and Linux compatibility before buying. This project has not tested or certified that microphone. Unlike the wired setup, the wireless microphone needs charging. See the manufacturer's [kit and compatibility information](https://onlinemanual.insta360.com/mic/en-us/specs/compatibility).

- Wireless microphone kit, including receiver: **[ADD AMAZON LINK HERE]**

After connecting either type, open **Ubuntu Settings → Sound → Input**, select it, and check that the input meter moves when you speak.

## Set it up

These instructions are for Ubuntu 26.04. You will need an internet connection for the supporting software and the first speech-model download. Everyday transcription then works offline.

1. On this GitHub page, choose **Code → Download ZIP**. Extract the downloaded folder.
2. Open a terminal in that folder. On Ubuntu, you can usually right-click inside the folder and choose **Open in Terminal**.
3. Install the supporting software by pasting this command. Ubuntu may ask for your computer password:

   ```sh
   sudo apt update
   sudo apt install whisper.cpp pipewire-bin bubblewrap python3-gi gir1.2-gtk-3.0 libglib2.0-bin gnome-shell-extension-prefs
   ```

4. Run the setup below **without sudo**. It downloads an English speech model of about 148 MB, checks the download, and installs the tools for your account:

   ```sh
   /usr/bin/python3 install.py
   ```

5. **Sign out of Ubuntu and sign back in once.** This lets GNOME load the global Ctrl+Shift+G shortcut.
6. Open a new Bash terminal if you want Ctrl+G dictation there. For Codex, start or resume Codex from that new terminal.

You can also find **Talk More, Type Less** in your applications menu.

The setup adds a short entry to your Bash startup file and keeps a copy of that file before the first change. It does not install Codex, change your Codex account, or include anyone's login details.

If a previous custom dictation setup is already present, setup stops instead of replacing it. Keep a backup and move the old setup aside before switching to this package. Do not run the installer over a working personal setup just to try the project.

### Other Linux desktops

The global shortcut currently supports **GNOME 50 only**. The recording window and terminal tools also depend on Wayland, PipeWire, and Ubuntu's supporting packages. Other combinations have not been tested.

To deliberately skip the GNOME shortcut, run:

```sh
/usr/bin/python3 install.py --no-shortcut
```

Use the applications menu to open the window. This does not promise a global shortcut on other desktops.

### Already have the English speech model?

You can use your existing `ggml-base.en.bin` instead of downloading it again:

```sh
/usr/bin/python3 install.py --model /path/to/ggml-base.en.bin
```

The file must match the model version this project checks. The model is distributed separately by the [whisper.cpp project](https://github.com/ggml-org/whisper.cpp/tree/master/models); it is not included in this repository.

## Everyday use

### In the dictation window

1. Press **Ctrl+Shift+G**.
2. Click **Clear text and record** and speak.
3. Click **Stop and transcribe**.
4. Read the result and make any corrections.
5. Click **Copy text**, switch to your app, and paste.

Most apps use **Ctrl+V** to paste. Ubuntu Terminal usually uses **Ctrl+Shift+V**. Keep the dictation window open until you have pasted the text.

### In Bash or Codex

1. Press **Ctrl+G** to start recording.
2. Speak, then press **Enter** to stop recording.
3. Wait for the transcription to appear in your draft.
4. Review it. Press **Enter again** only when you want to run the command or send the message.

**Ctrl+C while recording cancels that recording.** In Codex, the helper consumes the recording keys itself, so they are not sent as interrupt or submit keys to Codex. Keys typed while recording or waiting for transcription are ignored, apart from stopping or cancelling the recording.

At an ordinary Bash prompt, review dictated commands especially carefully before pressing Enter. Speech recognition can make mistakes.

The Ctrl+G Bash shortcut works at Bash's prompt, not inside every terminal program. The Codex helper applies to sessions launched through the supplied Bash integration. A Codex session that was already open will still use its previous setup.

## Spoken punctuation

| Say | Get |
| --- | --- |
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

For example, **“Hello comma how are you question mark”** becomes **“Hello, how are you?”**

This is a small text-conversion step after Whisper finishes. It does not call another AI service. It also removes nearby punctuation that Whisper may have added beside a spoken command.

These words act as commands even when you meant them literally. Uncheck **Spoken punctuation** in the window when you want the words themselves. Terminal dictation currently always converts them. Whisper may still guess punctuation elsewhere, and the conversion does not automatically fix spelling or capitalization.

## Privacy

Speech recognition runs on your computer. During ordinary use, the recording and transcription process runs with direct network access blocked and limited access to files. Temporary audio is removed after use; this project does not keep a transcript history.

The microphone is accessed through your desktop's audio service. The clipboard, terminal history, and apps where you paste or send text have their own behavior. **Sending a dictated prompt to Codex sends that text to Codex**, just as typing and submitting it would.

The first setup downloads the speech model. Nothing starts recording until you click the record button or press Ctrl+G.

## If something does not work

- **No microphone sound:** choose the correct input in Ubuntu's Sound settings and check the input meter first.
- **Ctrl+Shift+G does nothing:** sign out and back in after setup. Open the Extensions app and check that **Talk More, Type Less Shortcut** is enabled. Confirm you are using GNOME 50.
- **The shortcut is already used by something else:** remove the conflicting shortcut in Ubuntu's Keyboard settings. The extension owns Ctrl+Shift+G while enabled.
- **Ctrl+G still opens an editor or pauses Codex:** open a new Bash terminal and start Codex from there. Existing sessions do not pick up the new helper.
- **Words appear instead of punctuation:** in the window, check **Spoken punctuation**. Close and reopen any window left running from before an update.
- **A recording fails:** try a segment longer than a second. Recordings stop automatically after two minutes.
- **Transcription is slow:** speed depends on the computer. This setup uses the small English `base.en` model and the CPU.
- **A supporting package cannot be found:** these steps target Ubuntu 26.04. Other releases may not provide the same packages.

If you report a problem, include your Ubuntu version, desktop version, which shortcut you used, and what you expected to happen. Please do not attach private recordings or login information.

## Remove it

Open a terminal in the downloaded project folder and run:

```sh
/usr/bin/python3 uninstall.py
```

Then open a new terminal. The original Bash backup is kept. Existing windows and Codex sessions should be closed when you are ready; the remover does not forcibly stop your work.

## Project status and helping out

This is a small community starting point, not a polished app-store release. Recording and transcription have been used on an Ubuntu ARM64 setup. Automated checks cover punctuation, terminal draft insertion, cancellation, and keeping a simulated task running during recording. The GNOME handler has been checked with simulated windows; its behavior after login still needs hands-on confirmation. The new installer has been tested in temporary folders, not on a fresh Ubuntu installation.

Questions, bug reports, clearer instructions, and compatibility reports are welcome. See [Contributing](CONTRIBUTING.md). For the few technical checks used by contributors, see [Testing](tests/README.md).

## Thanks and license

Built using [whisper.cpp](https://github.com/ggml-org/whisper.cpp), [OpenAI Whisper](https://github.com/openai/whisper), GTK, PipeWire, Bubblewrap, and GNOME.

The original files in this project use the [MIT License](LICENSE). The supporting software and separately downloaded model keep their own licenses. This project is not an official OpenAI or Insta360 product.
