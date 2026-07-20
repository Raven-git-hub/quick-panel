"""
Terminal plugin — embeds a native VTE terminal widget.
Runs as a real in-process GTK widget rather than reparenting an
external window, so it works on both X11 and Wayland.
"""

PLUGIN_LABEL = 'Terminal'

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Vte', '2.91')
from gi.repository import Gtk, Gdk, GLib, Pango, Vte
import os

import config as cfg_module
import style as style_module


def build(tab: dict) -> Gtk.Widget:
    return TerminalPanel(tab).widget


class TerminalPanel:
    def __init__(self, tab: dict):
        self._tab = tab
        self.widget = self._build()
        self._spawn_shell()

    def _build(self) -> Gtk.Widget:
        self._root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._root.set_hexpand(True)
        self._root.set_vexpand(True)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        row.set_hexpand(True)
        row.set_vexpand(True)

        self._vte = Vte.Terminal()
        self._vte.set_hexpand(True)
        self._vte.set_vexpand(True)
        self._vte.set_scrollback_lines(10000)
        self._vte.set_mouse_autohide(True)
        self._vte.set_cursor_blink_mode(Vte.CursorBlinkMode.OFF)
        self._vte.set_allow_hyperlink(True)

        self._apply_theme()

        self._vte.connect('child-exited', self._on_child_exited)
        self._vte.connect('button-press-event', self._on_button_press)
        self._vte.connect('key-press-event', self._on_key_press)

        row.pack_start(self._vte, True, True, 0)

        scrollbar = Gtk.Scrollbar(
            orientation=Gtk.Orientation.VERTICAL,
            adjustment=self._vte.get_vadjustment(),
        )
        row.pack_start(scrollbar, False, False, 0)

        self._root.pack_start(row, True, True, 0)

        # Shown when the shell process exits
        self._exited_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self._exited_box.set_valign(Gtk.Align.CENTER)
        self._exited_box.set_halign(Gtk.Align.CENTER)
        self._exited_box.set_vexpand(True)
        self._exited_box.set_no_show_all(True)
        self._exited_box.hide()

        lbl = Gtk.Label(label='Shell exited.')
        lbl.get_style_context().add_class('form-label')
        self._exited_box.pack_start(lbl, False, False, 0)

        restart_btn = Gtk.Button(label='Restart')
        restart_btn.get_style_context().add_class('add-btn')
        restart_btn.set_relief(Gtk.ReliefStyle.NONE)
        restart_btn.set_halign(Gtk.Align.CENTER)
        restart_btn.connect('clicked', lambda _: self._restart())
        self._exited_box.pack_start(restart_btn, False, False, 0)

        self._root.pack_start(self._exited_box, True, True, 0)

        return self._root

    def _apply_theme(self):
        cfg = cfg_module.load()
        theme = style_module.get_theme(
            cfg.get('theme', style_module.DEFAULT_THEME))
        font_size = style_module.FONT_SIZES.get(
            cfg.get('font_size', style_module.DEFAULT_FONT),
            style_module.FONT_SIZES[style_module.DEFAULT_FONT],
        )

        bg = Gdk.RGBA()
        bg.parse(theme['bg_main'])
        fg = Gdk.RGBA()
        fg.parse(theme['text'])
        self._vte.set_color_background(bg)
        self._vte.set_color_foreground(fg)

        font_desc = Pango.FontDescription.from_string(
            f"Monospace {font_size + 1}")
        self._vte.set_font(font_desc)

    def _spawn_shell(self):
        shell = os.environ.get('SHELL', '/bin/bash')
        home  = os.path.expanduser('~')

        self._vte.spawn_async(
            Vte.PtyFlags.DEFAULT,
            home,
            [shell],
            [],
            GLib.SpawnFlags.DEFAULT,
            None,
            None,
            -1,
            None,
            self._on_spawn_complete,
        )

    def _on_spawn_complete(self, terminal, pid, error):
        if error:
            print(f"Terminal spawn error: {error}")

    def _on_child_exited(self, terminal, status):
        self._vte.hide()
        self._exited_box.show()

    def _restart(self):
        self._exited_box.hide()
        self._vte.show()
        self._vte.reset(True, True)
        self._spawn_shell()

    # ── Context menu ──────────────────────────────────────────────────────

    def _on_button_press(self, widget, event):
        if event.button == 3:
            self._show_context_menu(event)
            return True
        return False

    def _show_context_menu(self, event):
        menu = Gtk.Menu()

        copy_item = Gtk.MenuItem(label='Copy')
        copy_item.set_sensitive(self._vte.get_has_selection())
        copy_item.connect(
            'activate',
            lambda _: self._vte.copy_clipboard_format(Vte.Format.TEXT))
        menu.append(copy_item)

        paste_item = Gtk.MenuItem(label='Paste')
        paste_item.connect('activate', lambda _: self._vte.paste_clipboard())
        menu.append(paste_item)

        menu.append(Gtk.SeparatorMenuItem())

        clear_item = Gtk.MenuItem(label='Clear')
        clear_item.connect('activate', lambda _: self._vte.reset(True, True))
        menu.append(clear_item)

        menu.show_all()
        menu.popup_at_pointer(event)
        return True

    def _on_key_press(self, widget, event):
        state = event.state
        ctrl_shift = bool(state & Gdk.ModifierType.CONTROL_MASK) and \
                     bool(state & Gdk.ModifierType.SHIFT_MASK)
        if ctrl_shift:
            keyval = Gdk.keyval_to_lower(event.keyval)
            if keyval == Gdk.KEY_c and self._vte.get_has_selection():
                self._vte.copy_clipboard_format(Vte.Format.TEXT)
                return True
            if keyval == Gdk.KEY_v:
                self._vte.paste_clipboard()
                return True
        return False
