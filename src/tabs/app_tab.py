"""
App plugin — embeds an arbitrary installed application window into the
panel using X11 window reparenting via xdotool.

Wayland note: this only works for apps whose window ends up as an X11
surface — either via XWayland (the default compatibility path for
most non-GNOME apps today) or because we've nudged its toolkit toward
an X11 backend below. Apps that are strictly Wayland-native with no
X11 fallback cannot be embedded this way; there is currently no
equivalent embedding path for native Wayland surfaces in GTK3. If
embedding fails you'll see the retry/error state, not a crash.
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Gio
import subprocess


def build(tab: dict) -> Gtk.Widget:
    return AppPanel(tab).widget


class AppPanel:
    def __init__(self, tab: dict):
        self._tab            = tab
        self._embed_attempts = 0
        self._embedded_win   = None
        self._before_ids     = set()

        self.widget = self._build()
        GLib.timeout_add(300, self._launch_app)

    def _build(self) -> Gtk.Widget:
        self._root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._root.set_hexpand(True)
        self._root.set_vexpand(True)

        label = self._tab.get('label', 'this app')

        self._loading_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self._loading_box.set_valign(Gtk.Align.CENTER)
        self._loading_box.set_halign(Gtk.Align.CENTER)
        self._loading_box.set_vexpand(True)

        spinner = Gtk.Spinner()
        spinner.set_size_request(32, 32)
        spinner.start()
        self._loading_box.pack_start(spinner, False, False, 0)

        loading_label = Gtk.Label(label=f'Loading {label}…')
        loading_label.get_style_context().add_class('form-label')
        self._loading_box.pack_start(loading_label, False, False, 0)
        self._root.pack_start(self._loading_box, True, True, 0)

        self._socket = Gtk.Socket()
        self._socket.set_hexpand(True)
        self._socket.set_vexpand(True)
        self._socket.set_no_show_all(True)
        self._socket.hide()
        self._socket.connect('plug-removed', self._on_plug_removed)
        self._root.pack_start(self._socket, True, True, 0)

        self._error_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self._error_box.set_valign(Gtk.Align.CENTER)
        self._error_box.set_halign(Gtk.Align.CENTER)
        self._error_box.set_vexpand(True)
        self._error_box.set_no_show_all(True)
        self._error_box.hide()

        error_lbl = Gtk.Label(
            label=f'Could not embed {label}.\n'
                  'It may be running as a native Wayland window,\n'
                  'which cannot currently be embedded.')
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

    def _launch_app(self):
        app_id = self._tab.get('app_id')
        if not app_id:
            self._show_error()
            return False

        try:
            app_info = Gio.DesktopAppInfo.new(app_id)
        except Exception:
            app_info = None

        if not app_info:
            self._show_error()
            return False

        self._before_ids = self._get_window_ids()

        context = Gio.AppLaunchContext()
        context.setenv('GDK_BACKEND', 'x11')
        context.setenv('QT_QPA_PLATFORM', 'xcb')
        context.setenv('ELECTRON_OZONE_PLATFORM_HINT', 'x11')

        try:
            app_info.launch([], context)
        except Exception as e:
            print(f"App launch error ({app_id}): {e}")
            self._show_error()
            return False

        self._embed_attempts = 0
        GLib.timeout_add(800, self._try_embed)
        return False

    def _get_window_ids(self) -> set:
        try:
            result = subprocess.run(
                ['xdotool', 'search', '--onlyvisible', '--name', ''],
                capture_output=True, text=True, timeout=5
            )
            return {w for w in result.stdout.strip().split('\n') if w}
        except Exception:
            return set()

    def _try_embed(self):
        new_ids = self._get_window_ids() - self._before_ids

        if new_ids:
            win_id = int(sorted(new_ids)[-1])
            self._embed_window(win_id)
            return False

        self._embed_attempts += 1
        if self._embed_attempts > 20:
            self._show_error()
            return False

        return True

    def _embed_window(self, win_id: int):
        try:
            self._root.realize()
            self._socket.realize()
            socket_xid = self._socket.get_id()

            subprocess.run([
                'xdotool', 'set_window',
                '--overrideredirect', '1',
                str(win_id)
            ], timeout=3)

            subprocess.run([
                'xdotool', 'windowreparent',
                str(win_id),
                str(socket_xid)
            ], timeout=3)

            self._embedded_win = win_id
            self._loading_box.hide()
            self._error_box.hide()
            self._socket.show()

        except Exception as e:
            print(f"App reparent error: {e}")
            self._show_error()

    def _on_plug_removed(self, socket):
        self._socket.hide()
        self._error_box.hide()
        self._loading_box.show()
        self._embedded_win = None
        self._embed_attempts = 0
        GLib.timeout_add(1000, self._launch_app)
        return True

    def _on_retry(self, btn):
        self._error_box.hide()
        self._loading_box.show()
        self._embed_attempts = 0
        GLib.timeout_add(500, self._launch_app)

    def _show_error(self):
        self._loading_box.hide()
        self._socket.hide()
        self._error_box.show()
