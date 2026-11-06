# Local Whisper integration for interactive Bash sessions.
# Ctrl+G inserts literal transcription into Readline; it never accepts the line.
[[ $- == *i* ]] || return
__whisper_home="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

__whisper_insert_at_cursor() {
    local whisper_text
    if whisper_text="$("$__whisper_home/talk-more-type-less" --terminal --start)"; then
        # Keep Bash's character-aware indexing for UTF-8 prompt text.
        READLINE_LINE="${READLINE_LINE:0:READLINE_POINT}${whisper_text}${READLINE_LINE:READLINE_POINT}"
        READLINE_POINT=$((READLINE_POINT + ${#whisper_text}))
    fi
}

bind -m emacs-standard -x '"\C-g":__whisper_insert_at_cursor'
bind -m vi-insert -x '"\C-g":__whisper_insert_at_cursor'

# Keep Codex running while Ctrl+G records; insert only an unsent draft.
codex() {
    /usr/bin/python3 "$__whisper_home/codex-dictation" "$(type -P codex)" "$@"
}
