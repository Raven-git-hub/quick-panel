"""
Claude plugin — embeds a real Brave browser window into the panel
using X11 window embedding via GtkSocket. Bypasses Cloudflare/bot
detection because it literally is a real browser.
"""

PLUGIN_LABEL = 'Claude'

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import subprocess
import time


CLAUDE_URL    = 'https://claude.ai'
WINDOW_CLASS  = 'quickpanel-claude'


def build(tab: dict) -> Gtk.Widget:
    return ClaudePanel(tab).widget


class ClaudePanel:
    def __init__(self, tab: dict):
        self._tab         = tab
        self._brave_proc  = None
        self._socket      = None
        self._embed_tried = False

        self.widget = self._build()
        # Start brave and embed after a short delay
        GLib.timeout_add(500, self._launch_and_embed)

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

        loading_lbl = Gtk.Label(label='Loading Claude…')
        loading_lbl.get_style_context().add_class('form-label')
        self._loading_box.pack_start(loading_lbl, False, False, 0)

        self._root.pack_start(self._loading_box, True, True, 0)

        # Socket for embedding (hidden until ready)
        self._socket = Gtk.Socket()
        self._socket.set_hexpand(True)
        self._socket.set_vexpand(True)
        self._socket.set_no_show_all(True)
        self._socket.hide()
        self._socket.connect('plug-removed', self._on_plug_removed)
        self._root.pack_start(self._socket, True, True, 0)

        # Error state (hidden until needed)
        self._error_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self._error_box.set_valign(Gtk.Align.CENTER)
        self._error_box.set_halign(Gtk.Align.CENTER)
        self._error_box.set_vexpand(True)
        self._error_box.set_no_show_all(True)
        self._error_box.hide()

        error_lbl = Gtk.Label(label='Could not embed Claude.\nBrave may not be installed.')
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

    def _launch_and_embed(self):
        try:
            # Get the GtkSocket's X11 window ID for embedding
            self._root.realize()
            self._socket.realize()
            socket_id = self._socket.get_id()

            # Launch Brave in app mode, embedded into our socket
            self._brave_proc = subprocess.Popen([
                'brave-browser',
                f'--app={CLAUDE_URL}',
                f'--class={WINDOW_CLASS}',
                f'--window-size=1200,900',
                '--disable-session-crashed-bubble',
                '--disable-infobars',
                '--no-first-run',
                '--no-default-browser-check',
                f'--embedder-process-type={socket_id}',
                f'--plugin-window={socket_id}',
            ])

            # Poll for the window to appear and embed it
            GLib.timeout_add(1000, self._try_embed)

        except FileNotFoundError:
            self._show_error()

        return False  # don't repeat

    def _try_embed(self):
        if self._embed_tried:
            return False

        try:
            # Find the Brave window by class name
            result = subprocess.run(
                ['xdotool', 'search', '--class', WINDOW_CLASS],
                capture_output=True, text=True, timeout=5
            )
            window_ids = result.stdout.strip().split('\n')
            window_ids = [w for w in window_ids if w]

            if window_ids:
                win_id = int(window_ids[0])
                self._embed_window(win_id)
                self._embed_tried = True
                return False  # stop polling

            # Keep trying for up to 10 seconds
            if not hasattr(self, '_embed_attempts'):
                self._embed_attempts = 0
            self._embed_attempts += 1

            if self._embed_attempts > 10:
                self._show_error()
                return False

            return True  # keep polling

        except Exception as e:
            print(f"Claude plugin embed error: {e}")
            self._show_error()
            return False

    def _embed_window(self, win_id: int):
        try:
            # Remove decorations from the Brave window
            subprocess.run([
                'xdotool', 'set_window',
                '--name', 'claude-embedded',
                str(win_id)
            ])

            # Embed into our GTK socket
            self._socket.add_id(win_id)

            # Show the socket, hide loading
            self._loading_box.hide()
            self._socket.show()

        except Exception as e:
            print(f"Claude plugin embed window error: {e}")
            self._show_error()

    def _on_plug_removed(self, socket):
        """Called when the embedded window closes."""
        self._socket.hide()
        self._loading_box.show()
        self._embed_tried = False
        GLib.timeout_add(1000, self._launch_and_embed)
        return True

    def _on_retry(self, btn):
        self._error_box.hide()
        self._loading_box.show()
        self._embed_tried = False
        GLib.timeout_add(500, self._launch_and_embed)

    def _show_error(self):
        self._loading_box.hide()
        self._socket.hide()
        self._error_box.show()
