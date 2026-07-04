import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk

import config as cfg_module

# Width as fraction of screen width
WIDTH_FRACTIONS = {
    "quarter": 0.25,
    "half":    0.50,
    "full":    1.00,
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
    padding: 10px 0;
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
    padding: 10px 0;
    color: #4a5568;
}
.settings-btn:hover {
    background-color: #1a1d2e;
    color: #a0aec0;
}
"""


class Panel:
    def __init__(self, config: dict):
        self._config  = config
        self._visible = False
        self._active_idx = 0
        self._tab_buttons = []
        self._content_slots = []   # will hold tab widgets once tab types are built

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
        self.window.set_type_hint(Gdk.WindowTypeHint.DOCK)
        self.window.set_accept_focus(True)
        self.window.set_resizable(False)
        self.window.set_keep_above(True)
        self.window.set_decorated(False)
        self.window.set_skip_taskbar_hint(True)
        self.window.set_skip_pager_hint(True)

        self.window.connect('delete-event', lambda w, e: w.hide() or True)
        self.window.connect('key-press-event', self._on_key)

        # Root: icon strip | content
        root = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        root.pack_start(self._build_icon_strip(), False, False, 0)
        root.pack_start(self._build_content_area(), True, True, 0)

        self.window.add(root)

    def _build_icon_strip(self):
        strip = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        strip.get_style_context().add_class('icon-strip')
        strip.set_size_request(48, -1)

        tabs = self._config.get('tabs', [])
        for i, tab in enumerate(tabs):
            btn = self._make_tab_button(i, tab)
            strip.pack_start(btn, False, False, 0)
            self._tab_buttons.append(btn)

        # Spacer pushes settings icon to bottom
        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        strip.pack_start(spacer, True, True, 0)

        # Settings button
        settings_btn = Gtk.Button()
        settings_btn.get_style_context().add_class('settings-btn')
        settings_btn.set_relief(Gtk.ReliefStyle.NONE)
        settings_btn.set_tooltip_text('Settings')
        settings_btn.add(
            Gtk.Image.new_from_icon_name('preferences-system-symbolic',
                                          Gtk.IconSize.LARGE_TOOLBAR)
        )
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

        close_btn = Gtk.Button.new_from_icon_name(
            'window-close-symbolic', Gtk.IconSize.SMALL_TOOLBAR)
        close_btn.get_style_context().add_class('header-btn')
        close_btn.connect('clicked', lambda _: self.hide())

        reload_btn = Gtk.Button.new_from_icon_name(
            'view-refresh-symbolic', Gtk.IconSize.SMALL_TOOLBAR)
        reload_btn.get_style_context().add_class('header-btn')
        reload_btn.connect('clicked', self._reload_active)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header.get_style_context().add_class('header')
        header.pack_start(self._header_title, True, True, 0)
        header.pack_end(close_btn,   False, False, 4)
        header.pack_end(reload_btn,  False, False, 0)
        box.pack_start(header, False, False, 0)

        # Stack — tab content goes here (populated by tab type modules later)
        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.NONE)
        self._stack.set_hexpand(True)
        self._stack.set_vexpand(True)

        # Placeholder until tab types are wired in
        placeholder = Gtk.Label(label='No tabs configured')
        placeholder.set_valign(Gtk.Align.CENTER)
        self._stack.add_named(placeholder, 'placeholder')

        box.pack_start(self._stack, True, True, 0)
        return box

    def _make_tab_button(self, idx: int, tab: dict):
        btn = Gtk.Button()
        btn.get_style_context().add_class('tab-btn')
        btn.set_relief(Gtk.ReliefStyle.NONE)
        btn.set_tooltip_text(tab.get('label', f'Tab {idx}'))
        btn.add(
            Gtk.Image.new_from_icon_name(
                tab.get('icon', 'text-x-generic-symbolic'),
                Gtk.IconSize.LARGE_TOOLBAR,
            )
        )
        btn.connect('clicked', lambda _, i=idx: self._switch_to(i))
        return btn

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

    def _reload_active(self, *_):
        # Will be implemented once WebKit tabs are wired in
        pass

    # ── Settings ──────────────────────────────────────────────────────────────

    def _open_settings(self, *_):
        # Placeholder — settings panel coming next
        print("Settings: coming soon")

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

    def hide(self):
        self.window.hide()
        self._visible = False

    def _position_window(self):
        screen   = Gdk.Screen.get_default()
        monitor  = screen.get_primary_monitor()
        geo      = screen.get_monitor_geometry(monitor)

        fraction = WIDTH_FRACTIONS.get(self._config.get('width', 'half'), 0.5)
        width    = int(geo.width * fraction)

        self.window.resize(width, geo.height)
        self.window.move(geo.x + geo.width - width, geo.y)

    # ── Keyboard ──────────────────────────────────────────────────────────────

    def _on_key(self, _win, event):
        if event.keyval == Gdk.KEY_Escape:
            self.hide()
