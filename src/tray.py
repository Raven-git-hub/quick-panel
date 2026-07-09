"""
System tray icon with displayability detection.

GNOME Shell 42+ has no native tray: AppIndicator icons only render when a
StatusNotifier host is present (the ubuntu-appindicators extension). The
AppIndicator API gives no feedback when the icon is invisible, so we check
the session bus for org.kde.StatusNotifierWatcher — if no watcher owns that
name, the icon cannot appear and `self.available` is False. main.py uses
this to fall back to showing the panel at startup so the app is never
unreachable.
"""

import os

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GLib

# Try Ayatana (Ubuntu/Pop 22.04+) then fall back to AppIndicator3
try:
    gi.require_version('AyatanaAppIndicator3', '0.1')
    from gi.repository import AyatanaAppIndicator3 as AppIndicator3
except Exception:
    try:
        gi.require_version('AppIndicator3', '0.1')
        from gi.repository import AppIndicator3
    except Exception:
        AppIndicator3 = None


def _sni_watcher_present() -> bool:
    """True if a StatusNotifier watcher is on the session bus — i.e. an
    AppIndicator icon actually has somewhere to be displayed."""
    try:
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        result = bus.call_sync(
            'org.freedesktop.DBus',
            '/org/freedesktop/DBus',
            'org.freedesktop.DBus',
            'NameHasOwner',
            GLib.Variant('(s)', ('org.kde.StatusNotifierWatcher',)),
            GLib.VariantType('(b)'),
            Gio.DBusCallFlags.NONE,
            -1,
            None,
        )
        return bool(result.unpack()[0])
    except Exception:
        return False


def _status_icon_likely_visible() -> bool:
    """Gtk.StatusIcon (deprecated) only renders on desktops with a legacy
    X11 tray — never on GNOME 42+. Heuristic, not a guarantee."""
    desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').upper()
    session = os.environ.get('XDG_SESSION_TYPE', '').lower()
    return session == 'x11' and 'GNOME' not in desktop


class TrayIcon:
    def __init__(self, on_toggle, on_quit):
        self._on_toggle = on_toggle
        self._on_quit   = on_quit

        # Whether the icon can actually be displayed on this system.
        self.available = False

        if AppIndicator3:
            self._build_indicator()
            self.available = _sni_watcher_present()
        else:
            self._build_status_icon()
            self.available = _status_icon_likely_visible()

    def _build_indicator(self):
        self._indicator = AppIndicator3.Indicator.new(
            'quick-panel',
            'view-sidebar-symbolic',
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
        )
        self._indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self._indicator.set_menu(self._build_menu())

    def _build_status_icon(self):
        self._icon = Gtk.StatusIcon()
        self._icon.set_from_icon_name('view-sidebar-symbolic')
        self._icon.set_tooltip_text('Quick Panel')
        self._icon.connect('activate', lambda _: self._on_toggle())
        self._icon.connect('popup-menu', self._on_popup)

    def _on_popup(self, icon, button, time):
        menu = self._build_menu()
        menu.show_all()
        menu.popup(None, None, Gtk.StatusIcon.position_menu,
                   icon, button, time)

    def _build_menu(self):
        menu = Gtk.Menu()

        toggle = Gtk.MenuItem(label='Toggle Panel')
        toggle.connect('activate', lambda _: self._on_toggle())
        menu.append(toggle)

        menu.append(Gtk.SeparatorMenuItem())

        quit_item = Gtk.MenuItem(label='Quit')
        quit_item.connect('activate', lambda _: self._on_quit())
        menu.append(quit_item)

        menu.show_all()
        return menu
