import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import Meta from 'gi://Meta';
import Shell from 'gi://Shell';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';

const APP_ID = 'local.whisper.Dictation';
const KEY = 'open-whisper-dictation';

export default class DictationShortcut extends Extension {
    enable() {
        this._settings = this.getSettings();
        this._oldShortcut = new Gio.Settings({
            schema_id: 'org.gnome.settings-daemon.plugins.media-keys.custom-keybinding',
            path: '/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/whisper-dictation/',
        });
        const previous = this._oldShortcut.get_string('binding');
        if (previous)
            this._settings.set_string('previous-binding', previous);
        this._oldShortcut.set_string('binding', '');
        // Let the media-keys daemon release its old grab first.
        this._registerSource = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 500, () => {
            this._registerSource = 0;
            const action = Main.wm.addKeybinding(KEY, this._settings,
                Meta.KeyBindingFlags.IGNORE_AUTOREPEAT,
                Shell.ActionMode.NORMAL | Shell.ActionMode.OVERVIEW | Shell.ActionMode.POPUP,
                () => this._activate());
            if (action === Meta.KeyBindingAction.NONE) {
                this.disable();
                Main.notifyError('Whisper Dictation', 'Could not register the global dictation shortcut.');
            }
            return GLib.SOURCE_REMOVE;
        });
    }

    _activate() {
        const app = Shell.AppSystem.get_default().lookup_app(`${APP_ID}.desktop`);
        const windows = global.display.get_tab_list(Meta.TabList.NORMAL_ALL, null);
        const appWindows = app?.get_windows() ?? [];
        const window = windows.find(w => appWindows.includes(w) || w.get_wm_class() === APP_ID);
        Main.overview.hide();
        if (window) {
            // Shell activation switches workspaces, unminimizes and focuses directly.
            Main.activateWindow(window, global.get_current_time());
        } else if (app) {
            app.activate();
        } else {
            Main.notifyError('Whisper Dictation', 'The dictation desktop entry was not found.');
        }
    }

    disable() {
        if (this._registerSource) {
            GLib.Source.remove(this._registerSource);
            this._registerSource = 0;
        }
        Main.wm.removeKeybinding(KEY);
        if (this._oldShortcut && this._settings && !this._oldShortcut.get_string('binding'))
            this._oldShortcut.set_string('binding', this._settings.get_string('previous-binding'));
        this._oldShortcut = null;
        this._settings = null;
    }
}
