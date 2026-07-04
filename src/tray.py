import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

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


class TrayIcon:
    def __init__(self, on_toggle, on_quit):
        self._on_toggle = on_toggle
        self._on_quit   = on_quit

        if AppIndicator3:
            self._build_indicator()
        else:
            self._build_status_icon()

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
