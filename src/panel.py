import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, Pango, GLib

import config as cfg_module
import style as style_module

STRIP_WIDTH = 160

WIDTH_SETTINGS = {
    "narrow": (0.25, 600,  1000),
    "medium": (0.33, 800,  1200),
    "wide":   (0.50, 1000, 1800),
}

# Detect Wayland
_IS_WAYLAND = os.environ.get('XDG_SESSION_TYPE', '').lower() == 'wayland'

# Try to import GtkLayerShell for Wayland support
_LAYER_SHELL = None
if _IS_WAYLAND:
    try:
        gi.require_version('GtkLayerShell', '0.1')
        from gi.repository import GtkLayerShell
        _LAYER_SHELL = GtkLayerShell
    except Exception:
        pass


def _calculate_width(mode: str, screen_width: int) -> int:
    fraction, min_px, max_px = WIDTH_SETTINGS.get(mode, WIDTH_SETTINGS["medium"])
    width = int(screen_width * fraction)
    return max(min_px, min(max_px, width))


def _get_workarea():
    display = Gdk.Display.get_default()
    monitor = display.get_primary_monitor()
    if not monitor:
        monitor = display.get_monitor(0)
    return monitor.get_workarea()


class Panel:
    def __init__(self, config: dict):
        self._config             = config
        self._visible            = False
        self._active_idx         = 0
        self._tab_buttons        = []
        self._tab_widgets        = []
        self._tab_ids            = []
        self._panel_width        = None
        self._settings_open      = False

        self._apply_css()
        self._build_window()

    # ── CSS ───────────────────────────────────────────────────────────────────

    def _apply_css(self):
        css = style_module.generate_panel_css(
            self._config.get('theme', style_module.DEFAULT_THEME),
            self._config.get('font_size', style_module.DEFAULT_FONT),
            self._config.get('strip', 'left'),
        )
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )
        self._css_provider = provider

    def _refresh_css(self):
        css = style_module.generate_panel_css(
            self._config.get('theme', style_module.DEFAULT_THEME),
            self._config.get('font_size', style_module.DEFAULT_FONT),
            self._config.get('strip', 'left'),
        )
        self._css_provider.load_from_data(css.encode())

    # ── Window — created once, never destroyed ────────────────────────────────

    def _build_window(self):
        self.window = Gtk.Window()
        self.window.set_title('')
        self.window.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        self.window.set_accept_focus(True)
        self.window.set_resizable(False)
        self.window.set_keep_above(True)
        self.window.set_decorated(False)
        self.window.set_skip_taskbar_hint(True)
        self.window.set_skip_pager_hint(True)

        if _LAYER_SHELL:
            self._init_layer_shell()
        else:
            self.window.set_position(Gtk.WindowPosition.NONE)

        self.window.connect('delete-event', lambda w, e: w.hide() or True)
        self.window.connect('key-press-event', self._on_key)
        self.window.connect('realize', self._on_realize)

        # Root box — persists for life of app
        self._root = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.window.add(self._root)

        # Strip container — has the icon-strip CSS class, fixed width
        self._strip_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._strip_container.get_style_context().add_class('icon-strip')
        self._strip_container.set_size_request(STRIP_WIDTH, -1)

        # Content container — fills remaining space
        self._content_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._content_container.set_hexpand(True)
        self._content_container.set_vexpand(True)

        self._apply_strip_order()

        # Build header once
        self._build_header()

        # Build stack once
        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.NONE)
        self._stack.set_hexpand(True)
        self._stack.set_vexpand(True)
        self._stack.set_size_request(100, -1)
        self._content_container.pack_start(self._stack, True, True, 0)

        # Populate strip and stack
        self._populate_strip()
        self._populate_stack()

        self.window.show_all()

    def _apply_strip_order(self):
        for child in self._root.get_children():
            self._root.remove(child)

        strip_side = self._config.get('strip', 'left')
        if strip_side == 'right':
            self._root.pack_start(self._content_container, True,  True,  0)
            self._root.pack_start(self._strip_container,   False, False, 0)
        else:
            self._root.pack_start(self._strip_container,   False, False, 0)
            self._root.pack_start(self._content_container, True,  True,  0)

    def _build_header(self):
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
        header.pack_start(self._header_title, True,  True,  0)
        header.pack_end(close_btn,            False, False, 4)
        header.pack_end(reload_btn,           False, False, 0)

        self._content_container.pack_start(header, False, False, 0)

    # ── Strip — repopulated in place ──────────────────────────────────────────

    def _populate_strip(self):
        for child in self._strip_container.get_children():
            self._strip_container.remove(child)

        self._tab_buttons  = []
        tab_widget_idx     = 0
        tabs               = self._config.get('tabs', [])

        for tab in tabs:
            if tab.get('type') == 'divider':
                self._strip_container.pack_start(
                    self._make_divider_row(tab), False, False, 0)
            else:
                btn = self._make_tab_button(tab_widget_idx, tab)
                self._strip_container.pack_start(btn, False, False, 0)
                self._tab_buttons.append((tab['id'], btn))
                tab_widget_idx += 1

        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        self._strip_container.pack_start(spacer, True, True, 0)

        settings_btn = Gtk.Button()
        settings_btn.get_style_context().add_class('settings-btn')
        settings_btn.set_relief(Gtk.ReliefStyle.NONE)
        settings_btn.set_tooltip_text('Settings')

        settings_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
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
        self._strip_container.pack_end(settings_btn, False, False, 0)

        self._strip_container.show_all()

    # ── Stack — repopulated in place ──────────────────────────────────────────

    def _populate_stack(self):
        for name in [str(i) for i in range(100)] + ['placeholder']:
            child = self._stack.get_child_by_name(name)
            if child:
                self._stack.remove(child)

        self._tab_widgets = []
        self._tab_ids     = []

        tabs       = self._config.get('tabs', [])
        widget_idx = 0

        for tab in tabs:
            if tab.get('type') == 'divider':
                continue
            widget = self._build_tab_widget(tab)
            self._tab_widgets.append(widget)
            self._tab_ids.append(tab['id'])
            self._stack.add_named(widget, str(widget_idx))
            widget_idx += 1

        if not self._tab_widgets:
            placeholder = Gtk.Label(
                label='No tabs configured.\nClick Settings to add one.')
            placeholder.set_valign(Gtk.Align.CENTER)
            placeholder.set_halign(Gtk.Align.CENTER)
            placeholder.set_hexpand(True)
            placeholder.set_vexpand(True)
            self._stack.add_named(placeholder, 'placeholder')

        self._stack.show_all()

    def _make_divider_row(self, tab: dict) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        box.get_style_context().add_class('tab-btn')
        box.set_margin_start(8)
        box.set_margin_top(8)

        label_text = tab.get('label', '')
        if len(label_text) > 10:
            label_text = label_text[:10]

        lbl = Gtk.Label(label=label_text.upper())
        lbl.get_style_context().add_class('divider-label')
        lbl.set_halign(Gtk.Align.START)
        lbl.set_ellipsize(Pango.EllipsizeMode.END)
        lbl.set_max_width_chars(10)
        box.pack_start(lbl, True, True, 0)

        return box

    def _make_tab_button(self, idx: int, tab: dict) -> Gtk.Button:
        btn = Gtk.Button()
        btn.get_style_context().add_class('tab-btn')
        btn.set_relief(Gtk.ReliefStyle.NONE)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row.set_margin_start(8)

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
        from tabs import document_tab
        tab_type = tab.get('type', 'web')

        if tab_type in ('web', 'preset'):
            return web_tab.build(tab)
        if tab_type == 'files':
            return file_tab.build(tab)
        if tab_type == 'custom':
            return custom_tab.build(tab)
        if tab_type == 'document':
            return document_tab.build(tab)

        placeholder = Gtk.Label(
            label=f"Tab type '{tab_type}' not yet supported.")
        placeholder.set_valign(Gtk.Align.CENTER)
        placeholder.set_hexpand(True)
        placeholder.set_vexpand(True)
        return placeholder

    # ── Tab switching ─────────────────────────────────────────────────────────

    def _switch_to(self, idx: int):
        self._active_idx = idx
        if idx < len(self._tab_ids):
            tab_id = self._tab_ids[idx]
            for tab in self._config.get('tabs', []):
                if tab.get('id') == tab_id:
                    self._header_title.set_text(tab.get('label', ''))
                    break
            self._stack.set_visible_child_name(str(idx))

        for i, (tid, btn) in enumerate(self._tab_buttons):
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
        self._settings_open = True

        sp = SettingsPanel(
            config=self._config,
            on_back=self._close_settings,
            on_config_changed=self._on_config_changed,
        )

        existing = self._stack.get_child_by_name('settings')
        if existing:
            self._stack.remove(existing)

        self._stack.add_named(sp.widget, 'settings')
        self._stack.show_all()
        self._stack.set_visible_child_name('settings')
        self._header_title.set_text('Settings')

    def _close_settings(self):
        self._settings_open = False
        if self._tab_widgets:
            self._switch_to(self._active_idx)
        else:
            child = self._stack.get_child_by_name('placeholder')
            if child:
                self._stack.set_visible_child_name('placeholder')
            self._header_title.set_text('')

    def _on_config_changed(self, new_config):
        old_width    = self._config.get('width',    'medium')
        old_position = self._config.get('position', 'right')
        old_strip    = self._config.get('strip',    'left')
        new_width    = new_config.get('width',    'medium')
        new_position = new_config.get('position', 'right')
        new_strip    = new_config.get('strip',    'left')

        self._config = new_config
        self._refresh_css()

        if old_strip != new_strip:
            self._apply_strip_order()
            self._root.show_all()

        if old_position != new_position:
            if _LAYER_SHELL:
                self._apply_layer_shell_position()
            else:
                self._position_window()

        if old_width != new_width:
            self._position_window()

        self._populate_strip()
        self._populate_stack()

        if self._settings_open:
            GLib.idle_add(self._open_settings)

    # ── Layer shell ───────────────────────────────────────────────────────────

    def _init_layer_shell(self):
        _LAYER_SHELL.init_for_window(self.window)
        _LAYER_SHELL.set_layer(self.window, _LAYER_SHELL.Layer.TOP)
        _LAYER_SHELL.set_keyboard_mode(
            self.window, _LAYER_SHELL.KeyboardMode.ON_DEMAND)
        _LAYER_SHELL.set_anchor(self.window, _LAYER_SHELL.Edge.TOP,    True)
        _LAYER_SHELL.set_anchor(self.window, _LAYER_SHELL.Edge.BOTTOM, True)
        # Start with no exclusive zone until shown
        _LAYER_SHELL.set_exclusive_zone(self.window, 0)
        self._apply_layer_shell_position()

    def _apply_layer_shell_position(self):
        if not _LAYER_SHELL:
            return
        position = self._config.get('position', 'right')
        _LAYER_SHELL.set_anchor(
            self.window, _LAYER_SHELL.Edge.LEFT,  position == 'left')
        _LAYER_SHELL.set_anchor(
            self.window, _LAYER_SHELL.Edge.RIGHT, position == 'right')

    # ── Visibility ────────────────────────────────────────────────────────────

    def toggle(self):
        if self._visible:
            self.hide()
        else:
            self.show()

    def show(self):
        self._position_window()
        if _LAYER_SHELL:
            _LAYER_SHELL.set_exclusive_zone(self.window, self._panel_width)
        self.window.show_all()
        self._visible = True
        if self._tab_widgets:
            self._switch_to(self._active_idx)
        self.window.present()
        self._focus_active_webview()

    def hide(self):
        if _LAYER_SHELL:
            _LAYER_SHELL.set_exclusive_zone(self.window, 0)
        self.window.hide()
        self._visible = False

    def _on_realize(self, _widget):
        self._position_window()

    def _position_window(self):
        workarea = _get_workarea()
        mode = self._config.get('width', 'medium')
        self._panel_width = _calculate_width(mode, workarea.width)

        if _LAYER_SHELL:
            self._apply_layer_shell_position()
            self.window.set_size_request(self._panel_width, -1)
            if self._visible:
                _LAYER_SHELL.set_exclusive_zone(self.window, self._panel_width)
        else:
            height = workarea.height
            self.window.set_size_request(self._panel_width, height)
            self.window.resize(self._panel_width, height)
            self._move_window(workarea)

    def _move_window(self, workarea):
        position = self._config.get('position', 'right')
        if position == 'left':
            self.window.move(workarea.x, workarea.y)
        else:
            self.window.move(
                workarea.x + workarea.width - self._panel_width,
                workarea.y
            )

    def _on_key(self, _win, event):
        if event.keyval == Gdk.KEY_Escape:
            self.hide()
