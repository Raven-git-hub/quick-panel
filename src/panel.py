import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, Pango

import config as cfg_module

# Icon strip width
STRIP_WIDTH = 160

# Dynamic width settings per mode
# Each entry: (fraction, min_px, max_px)
WIDTH_SETTINGS = {
    "narrow": (0.20, 400,  550),
    "medium": (0.28, 550,  780),
    "wide":   (0.38, 780, 1100),
}

CSS = """
window {
    background-color: #0f1117;
}
.icon-strip {
    background-color: #080a0f;
    border-right: 1px solid #1e2130;
}
.tab-btn {
    background: transparent;
    border: none;
    border-radius: 0;
    padding: 8px 10px;
    color: #4a5568;
}
.tab-btn:hover {
    background-color: #1a1d2e;
    color: #a0aec0;
}
.tab-btn.active {
    background-color: #1a1d2e;
    color: #6366f1;
    border-left: 2px solid #6366f1;
}
.tab-label {
    color: #4a5568;
    font-size: 11px;
}
.tab-btn:hover .tab-label {
    color: #a0aec0;
}
.tab-btn.active .tab-label {
    color: #6366f1;
}
.header {
    background-color: #080a0f;
    border-bottom: 1px solid #1e2130;
    min-height: 38px;
}
.header-title {
    color: #e2e8f0;
    font-size: 13px;
    font-weight: 500;
}
.header-btn {
    background: transparent;
    border: none;
    border-radius: 4px;
    color: #4a5568;
    padding: 4px;
    min-width: 28px;
    min-height: 28px;
}
.header-btn:hover {
    background-color: #2d3748;
    color: #e2e8f0;
}
.settings-btn {
    background: transparent;
    border: none;
    border-radius: 0;
    padding: 8px 10px;
    color: #4a5568;
}
.settings-btn:hover {
    background-color: #1a1d2e;
    color: #a0aec0;
}
"""


def _calculate_width(mode: str, screen_width: int) -> int:
    """Calculate panel width dynamically based on screen size and mode."""
    fraction, min_px, max_px = WIDTH_SETTINGS.get(mode, WIDTH_SETTINGS["medium"])
    width = int(screen_width * fraction)
    return max(min_px, min(max_px, width))


class Panel:
    def __init__(self, config: dict):
        self._config      = config
        self._visible     = False
        self._active_idx  = 0
        self._tab_buttons = []
        self._tab_widgets = []
        self._realized    = False

        self._apply_css()
        self._build()

    # ── CSS ───────────────────────────────────────────────────────────────────

    def _apply_css(self):
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        self.window = Gtk.Window()
        self.window.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        self.window.set_accept_focus(True)
        self.window.set_resizable(False)
        self.window.set_keep_above(True)
        self.window.set_decorated(False)
        self.window.set_skip_taskbar_hint(True)
        self.window.set_skip_pager_hint(True)

        self.window.connect('delete-event', lambda w, e: w.hide() or True)
        self.window.connect('key-press-event', self._on_key)
        self.window.connect('realize', self._on_realize)

        root = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        root.pack_start(self._build_icon_strip(), False, False, 0)
        root.pack_start(self._build_content_area(), True, True, 0)

        self.window.add(root)

    def _build_icon_strip(self):
        strip = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        strip.get_style_context().add_class('icon-strip')
        strip.set_size_request(STRIP_WIDTH, -1)

        for i, tab in enumerate(self._config.get('tabs', [])):
            btn = self._make_tab_button(i, tab)
            strip.pack_start(btn, False, False, 0)
            self._tab_buttons.append(btn)

        # Spacer pushes settings to bottom
        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        strip.pack_start(spacer, True, True, 0)

        # Settings button
        settings_btn = Gtk.Button()
        settings_btn.get_style_context().add_class('settings-btn')
        settings_btn.set_relief(Gtk.ReliefStyle.NONE)
        settings_btn.set_tooltip_text('Settings')

        settings_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        settings_box.pack_start(
            Gtk.Image.new_from_icon_name(
                'preferences-system-symbolic',
                Gtk.IconSize.SMALL_TOOLBAR,
            ), False, False, 0)
        settings_lbl = Gtk.Label(label='Settings')
        settings_lbl.get_style_context().add_class('tab-label')
        settings_lbl.set_halign(Gtk.Align.START)
        settings_box.pack_start(settings_lbl, False, False, 0)
        settings_btn.add(settings_box)
        settings_btn.connect('clicked', self._open_settings)
        strip.pack_end(settings_btn, False, False, 0)

        return strip

    def _build_content_area(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_hexpand(True)
        box.set_vexpand(True)

        # Header
        self._header_title = Gtk.Label(label='')
        self._header_title.get_style_context().add_class('header-title')
        self._header_title.set_halign(Gtk.Align.START)
        self._header_title.set_margin_start(12)
        self._header_title.set_hexpand(True)

        reload_btn = Gtk.Button.new_from_icon_name(
            'view-refresh-symbolic', Gtk.IconSize.SMALL_TOOLBAR)
        reload_btn.get_style_context().add_class('header-btn')
        reload_btn.connect('clicked', self._reload_active)

        close_btn = Gtk.Button.new_from_icon_name(
            'window-close-symbolic', Gtk.IconSize.SMALL_TOOLBAR)
        close_btn.get_style_context().add_class('header-btn')
        close_btn.connect('clicked', lambda _: self.hide())

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header.get_style_context().add_class('header')
        header.pack_start(self._header_title, True, True, 0)
        header.pack_end(close_btn,  False, False, 4)
        header.pack_end(reload_btn, False, False, 0)
        box.pack_start(header, False, False, 0)

        # Stack — one slot per tab
        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.NONE)
        self._stack.set_hexpand(True)
        self._stack.set_vexpand(True)

        for i, tab in enumerate(self._config.get('tabs', [])):
            widget = self._build_tab_widget(tab)
            self._tab_widgets.append(widget)
            self._stack.add_named(widget, str(i))

        if not self._tab_widgets:
            placeholder = Gtk.Label(
                label='No tabs configured.\nClick Settings to add one.')
            placeholder.set_valign(Gtk.Align.CENTER)
            self._stack.add_named(placeholder, 'placeholder')

        box.pack_start(self._stack, True, True, 0)
        return box

    def _make_tab_button(self, idx: int, tab: dict) -> Gtk.Button:
        btn = Gtk.Button()
        btn.get_style_context().add_class('tab-btn')
        btn.set_relief(Gtk.ReliefStyle.NONE)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        icon = Gtk.Image.new_from_icon_name(
            tab.get('icon', 'text-x-generic-symbolic'),
            Gtk.IconSize.SMALL_TOOLBAR,
        )
        row.pack_start(icon, False, False, 0)

        label_text = tab.get('label', f'Tab {idx}')
        if len(label_text) > 10:
            label_text = label_text[:10]

        lbl = Gtk.Label(label=label_text)
        lbl.get_style_context().add_class('tab-label')
        lbl.set_halign(Gtk.Align.START)
        lbl.set_ellipsize(Pango.EllipsizeMode.END)
        lbl.set_max_width_chars(10)
        row.pack_start(lbl, True, True, 0)

        btn.add(row)
        btn.connect('clicked', lambda _, i=idx: self._switch_to(i))
        return btn

    def _build_tab_widget(self, tab: dict) -> Gtk.Widget:
        from tabs import web_tab
        from tabs import file_tab
        from tabs import custom as custom_tab
        tab_type = tab.get('type', 'web')

        if tab_type in ('web', 'preset'):
            return web_tab.build(tab)

        if tab_type == 'files':
            return file_tab.build(tab)

        if tab_type == 'custom':
            return custom_tab.build(tab)

        placeholder = Gtk.Label(
            label=f"Tab type '{tab_type}' not yet supported.")
        placeholder.set_valign(Gtk.Align.CENTER)
        return placeholder

    # ── Tab switching ─────────────────────────────────────────────────────────

    def _switch_to(self, idx: int):
        self._active_idx = idx
        tabs = self._config.get('tabs', [])
        if idx < len(tabs):
            self._header_title.set_text(tabs[idx].get('label', ''))
            self._stack.set_visible_child_name(str(idx))

        for i, btn in enumerate(self._tab_buttons):
            ctx = btn.get_style_context()
            if i == idx:
                ctx.add_class('active')
            else:
                ctx.remove_class('active')

        self._focus_active_webview()

    # ── Reload ────────────────────────────────────────────────────────────────

    def _reload_active(self, *_):
        from tabs import web_tab
        if self._active_idx < len(self._tab_widgets):
            web_tab.reload(self._tab_widgets[self._active_idx])

    # ── Focus ─────────────────────────────────────────────────────────────────

    def _focus_active_webview(self):
        if self._active_idx < len(self._tab_widgets):
            widget = self._tab_widgets[self._active_idx]
            widget.grab_focus()

    # ── Settings ──────────────────────────────────────────────────────────────

    def _open_settings(self, *_):
        from settings.settings_panel import SettingsPanel

        sp = SettingsPanel(
            config=self._config,
            on_back=self._close_settings,
            on_config_changed=self._on_config_changed,
        )

        if self._stack.get_child_by_name('settings'):
            self._stack.remove(self._stack.get_child_by_name('settings'))

        self._stack.add_named(sp.widget, 'settings')
        self._stack.show_all()
        self._stack.set_visible_child_name('settings')
        self._header_title.set_text('Settings')

    def _close_settings(self):
        if self._tab_widgets:
            self._switch_to(self._active_idx)
        else:
            self._stack.set_visible_child_name('placeholder')
            self._header_title.set_text('')

    def _on_config_changed(self, new_config):
        self._config = new_config
        self._rebuild()

    def _rebuild(self):
        self._tab_buttons = []
        self._tab_widgets = []

        for child in self.window.get_children():
            self.window.remove(child)

        root = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        root.pack_start(self._build_icon_strip(), False, False, 0)
        root.pack_start(self._build_content_area(), True, True, 0)
        self.window.add(root)
        self.window.show_all()

        self._open_settings()

    # ── Visibility ────────────────────────────────────────────────────────────

    def toggle(self):
        if self._visible:
            self.hide()
        else:
            self.show()

    def show(self):
        self._position_window()
        self.window.show_all()
        self._visible = True
        if self._tab_buttons:
            self._switch_to(self._active_idx)
        self.window.present()
        self._focus_active_webview()

    def hide(self):
        self.window.hide()
        self._visible = False

    def _on_realize(self, _widget):
        self._realized = True
        self._position_window()

    def _position_window(self):
        screen   = Gdk.Screen.get_default()
        monitor  = screen.get_primary_monitor()
        workarea = screen.get_monitor_workarea(monitor)

        mode  = self._config.get('width', 'medium')
        width = _calculate_width(mode, workarea.width)
        height = workarea.height

        self.window.set_size_request(width, height)
        self.window.resize(width, height)
        self.window.move(workarea.x + workarea.width - width, workarea.y)

    # ── Keyboard ──────────────────────────────────────────────────────────────

    def _on_key(self, _win, event):
        if event.keyval == Gdk.KEY_Escape:
            self.hide()
