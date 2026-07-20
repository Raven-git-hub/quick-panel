"""
App plugin — embeds an arbitrary installed application window into the
panel using X11 window reparenting via xdotool.

Rather than diffing window lists before/after launch (which fails for
single-instance apps like Discord/Spotify — launching a second time
just forwards to the running instance via IPC and exits without
creating a new window), this searches directly for a window matching
the target app's WM_CLASS or name, whether it was just created or
already existed and got focused.

Wayland note: this only works for apps whose window ends up as an X11
surface — either via XWayland or because we've nudged its toolkit
toward an X11 backend below. Apps that are strictly Wayland-native
with no X11 fallback cannot be embedded this way. Additionally, some
newer/non-mature Wayland compositors may not fully support legacy X11
reparenting for XWayland clients even when the window is visible to
X11 tooling — if embedding still fails after this fix, that's the
next thing to rule out.
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Gio
import subprocess


def build(tab: dict) -> Gtk.Widget:
    return AppPanel(tab).widget


class AppPanel:
    # Skip tiny helper/tray/tooltip windows some apps (esp. Electron)
    # spawn alongside their main window.
    MIN_WINDOW_AREA = 40000  # roughly 200x200px

    def __init__(self, tab: dict):
        self._tab            = tab
        self._embed_attempts = 0
        self._embedded_win   = None
        self._search_terms   = []

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
                  'or the compositor may not support reparenting.')
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

    def _get_search_terms(self, app_info) -> list:
        """Candidate strings to match against WM_CLASS / window name."""
        terms = []

        wm_class = app_info.get_startup_wm_class()
        if wm_class:
            terms.append(wm_class)

        app_id = self._tab.get('app_id', '')
        if app_id.endswith('.desktop'):
            app_id = app_id[:-len('.desktop')]
        if app_id:
            terms.append(app_id)

        label = self._tab.get('label', '')
        if label:
            terms.append(label.split()[0])

        seen, uniq = set(), []
        for t in terms:
            key = t.lower()
            if key and key not in seen:
                seen.add(key)
                uniq.append(t)
        return uniq

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

        self._search_terms = self._get_search_terms(app_info)

        context = Gio.AppLaunchContext()
        context.setenv('GDK_BACKEND', 'x11')
        context.setenv('QT_QPA_PLATFORM', 'xcb')
        context.setenv('ELECTRON_OZONE_PLATFORM_HINT', 'x11')

        try:
            # For single-instance apps already running, this just
            # forwards to the existing process via IPC and focuses its
            # window rather than creating a new one — we don't rely on
            # "a new window appeared," we search for a match afterward
            # regardless of whether it's new or pre-existing.
            app_info.launch([], context)
        except Exception as e:
            print(f"App launch error ({app_id}): {e}")
            self._show_error()
            return False

        self._embed_attempts = 0
        GLib.timeout_add(800, self._try_embed)
        return False

    def _find_matching_window(self):
        """Search by both WM_CLASS and window name for any candidate
        term, then return the largest matching visible window (to
        skip tiny helper/tray/tooltip windows some apps spawn)."""
        candidate_ids = set()

        for term in self._search_terms:
            for flag in ('--class', '--name'):
                try:
                    result = subprocess.run(
                        ['xdotool', 'search', '--onlyvisible', flag, term],
                        capture_output=True, text=True, timeout=5
                    )
                    for w in result.stdout.strip().split('\n'):
                        if w:
                            candidate_ids.add(w)
                except Exception:
                    pass

        if not candidate_ids:
            return None

        best_id, best_area = None, 0
        for win_id in candidate_ids:
            try:
                geo = subprocess.run(
                    ['xdotool', 'getwindowgeometry', '--shell', win_id],
                    capture_output=True, text=True, timeout=3
                )
                width = height = 0
                for line in geo.stdout.splitlines():
                    if line.startswith('WIDTH='):
                        width = int(line.split('=')[1])
                    elif line.startswith('HEIGHT='):
                        height = int(line.split('=')[1])
                area = width * height
                if area > best_area:
                    best_area = area
                    best_id = win_id
            except Exception:
                continue

        if best_id and best_area >= self.MIN_WINDOW_AREA:
            return int(best_id)
        return None

    def _try_embed(self):
        win_id = self._find_matching_window()

        if win_id:
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
