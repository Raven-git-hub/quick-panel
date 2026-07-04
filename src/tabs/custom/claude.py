"""
Claude plugin — embeds a real Brave browser window into the panel
using X11 window reparenting via xdotool.
"""

PLUGIN_LABEL = 'Claude'

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import subprocess


CLAUDE_URL   = 'https://claude.ai'
WINDOW_CLASS = 'quickpanel-claude'


def build(tab: dict) -> Gtk.Widget:
    return ClaudePanel(tab).widget


class ClaudePanel:
    def __init__(self, tab: dict):
        self._brave_proc     = None
        self._embed_attempts = 0
        self._embedded_win   = None

        self.widget = self._build()
        GLib.timeout_add(300, self._launch_brave)

    def _build(self) -> Gtk.Widget:
        self._root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._root.set_hexpand(True)
        self._root.set_vexpand(True)

        # Loading state
        self._loading_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self._loading_box.set_valign(Gtk.Align.CENTER)
        self._loading_box.set_halign(Gtk.Align.CENTER)
        self._loading_box.set_vexpand(True)

        spinner = Gtk.Spinner()
        spinner.set_size_request(32, 32)
        spinner.start()
        self._loading_box.pack_start(spinner, False, False, 0)

        lbl = Gtk.Label(label='Loading Claude…')
        lbl.get_style_context().add_class('form-label')
        self._loading_box.pack_start(lbl, False, False, 0)
        self._root.pack_start(self._loading_box, True, True, 0)

        # Socket for X11 embedding
        self._socket = Gtk.Socket()
        self._socket.set_hexpand(True)
        self._socket.set_vexpand(True)
        self._socket.set_no_show_all(True)
        self._socket.hide()
        self._socket.connect('plug-removed', self._on_plug_removed)
        self._root.pack_start(self._socket, True, True, 0)

        # Error state
        self._error_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self._error_box.set_valign(Gtk.Align.CENTER)
        self._error_box.set_halign(Gtk.Align.CENTER)
        self._error_box.set_vexpand(True)
        self._error_box.set_no_show_all(True)
        self._error_box.hide()

        error_lbl = Gtk.Label(label='Could not embed Claude.')
        error_lbl.set_justify(Gtk.Justification.CENTER)
        error_lbl.get_style_context().add_class('form-label')
        self._error_box.pack_start(error_lbl, False, False, 0)

        retry_btn = Gtk.Button(label='Retry')
        retry_btn.get_style_context().add_class('add-btn')
        retry_btn.set_relief(Gtk.ReliefStyle.NONE)
        retry_btn.set_halign(Gtk.Align.CENTER)
        retry_btn.connect('clicked', self._on_retry)
        self._error_box.pack_start(retry_btn, False, False, 0)
        self._root.pack_start(self._error_box, True, True, 0)

        return self._root

    def _launch_brave(self):
        try:
            self._brave_proc = subprocess.Popen([
                'brave-browser',
                f'--app={CLAUDE_URL}',
                f'--class={WINDOW_CLASS}',
                '--disable-session-crashed-bubble',
                '--disable-infobars',
                '--no-first-run',
                '--no-default-browser-check',
            ])
            self._embed_attempts = 0
            GLib.timeout_add(1500, self._try_embed)
        except FileNotFoundError:
            self._show_error()
        return False

    def _try_embed(self):
        try:
            result = subprocess.run(
                ['xdotool', 'search', '--class', WINDOW_CLASS],
                capture_output=True, text=True, timeout=5
            )
            window_ids = [w for w in result.stdout.strip().split('\n') if w]

            if window_ids:
                win_id = int(window_ids[-1])  # take the last one
                self._embed_window(win_id)
                return False

            self._embed_attempts += 1
            if self._embed_attempts > 15:
                self._show_error()
                return False

            return True  # keep polling

        except Exception as e:
            print(f"Claude embed error: {e}")
            self._embed_attempts += 1
            if self._embed_attempts > 15:
                self._show_error()
                return False
            return True

    def _embed_window(self, win_id: int):
        try:
            self._root.realize()
            self._socket.realize()
            socket_xid = self._socket.get_id()

            # Remove window decorations
            subprocess.run([
                'xdotool', 'set_window',
                '--overrideredirect', '1',
                str(win_id)
            ], timeout=3)

            # Reparent the Brave window into our GTK socket
            subprocess.run([
                'xdotool', 'windowreparent',
                str(win_id),
                str(socket_xid)
            ], timeout=3)

            self._embedded_win = win_id
            self._loading_box.hide()
            self._socket.show()

        except Exception as e:
            print(f"Claude reparent error: {e}")
            self._show_error()

    def _on_plug_removed(self, socket):
        self._socket.hide()
        self._loading_box.show()
        self._embedded_win = None
        self._embed_attempts = 0
        GLib.timeout_add(1000, self._launch_brave)
        return True

    def _on_retry(self, btn):
        self._error_box.hide()
        self._loading_box.show()
        self._embed_attempts = 0
        if self._brave_proc:
            self._brave_proc.kill()
        GLib.timeout_add(500, self._launch_brave)

    def _show_error(self):
        self._loading_box.hide()
        self._socket.hide()
        self._error_box.show()
