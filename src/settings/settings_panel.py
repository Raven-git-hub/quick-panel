import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
import uuid
import config as cfg_module
import style as style_module

ICON_OPTIONS = [
    ('network-server-symbolic',           'Server'),
    ('system-search-symbolic',            'Search'),
    ('applications-science-symbolic',     'Science'),
    ('audio-x-generic-symbolic',          'Music'),
    ('folder-symbolic',                   'Folder'),
    ('emblem-system-symbolic',            'System'),
    ('user-home-symbolic',                'Home'),
    ('utilities-system-monitor-symbolic', 'Monitor'),
    ('web-browser-symbolic',              'Browser'),
    ('mail-symbolic',                     'Mail'),
    ('camera-symbolic',                   'Camera'),
    ('preferences-system-symbolic',       'Settings'),
]


class SettingsPanel:
    def __init__(self, config: dict, on_back, on_config_changed):
        self._config            = config
        self._on_back           = on_back
        self._on_config_changed = on_config_changed
        self._selected_icon     = ICON_OPTIONS[0][0]
        self._width_buttons     = {}
        self._font_buttons      = {}
        self._position_buttons  = {}
        self._strip_buttons     = {}
        self._presets           = []
        self._available_apps    = []
        self._selected_app_id   = None
        self._css_provider      = None
        self._icon_buttons      = {}

        self._apply_css()
        self._load_presets()
        self.widget = self._build()

    def _apply_css(self):
        css = style_module.generate_settings_css(
            self._config.get('theme', style_module.DEFAULT_THEME),
            self._config.get('font_size', style_module.DEFAULT_FONT),
        )
        self._css_provider = Gtk.CssProvider()
        self._css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            self._css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def _refresh_css(self):
        css = style_module.generate_settings_css(
            self._config.get('theme', style_module.DEFAULT_THEME),
            self._config.get('font_size', style_module.DEFAULT_FONT),
        )
        self._css_provider.load_from_data(css.encode())

    def _load_presets(self):
        try:
            from tabs.presets import load_all
            self._presets = load_all()
        except Exception as e:
            print(f"Warning: could not load presets: {e}")
            self._presets = []

    def _build(self) -> Gtk.Widget:
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        root.get_style_context().add_class('settings-root')
        root.set_hexpand(True)
        root.set_vexpand(True)

        root.pack_start(self._build_header(), False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content.set_margin_start(16)
        content.set_margin_end(16)
        content.set_margin_top(16)
        content.set_margin_bottom(16)

        content.pack_start(self._build_appearance_section(), False, False, 0)
        content.pack_start(self._build_layout_section(),     False, False, 0)
        content.pack_start(self._build_startup_section(),    False, False, 0)
        content.pack_start(self._build_tabs_section(),       False, False, 0)
        content.pack_start(self._build_add_section(),        False, False, 0)
        content.pack_start(self._build_divider_section(),    False, False, 0)

        scroll.add(content)
        root.pack_start(scroll, True, True, 0)
        return root

    def _build_header(self) -> Gtk.Widget:
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header.set_margin_start(8)
        header.set_margin_end(8)
        header.set_margin_top(4)
        header.set_margin_bottom(4)

        back_btn = Gtk.Button(label='← Back')
        back_btn.get_style_context().add_class('back-btn')
        back_btn.set_relief(Gtk.ReliefStyle.NONE)
        back_btn.connect('clicked', lambda _: self._on_back())
        header.pack_start(back_btn, False, False, 0)

        title = Gtk.Label(label='Settings')
        title.get_style_context().add_class('header-title')
        title.set_halign(Gtk.Align.CENTER)
        title.set_hexpand(True)
        header.pack_start(title, True, True, 0)

        spacer = Gtk.Box()
        spacer.set_size_request(60, -1)
        header.pack_end(spacer, False, False, 0)

        sep = Gtk.Separator()
        sep.get_style_context().add_class('divider')

        wrap = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        wrap.pack_start(header, False, False, 0)
        wrap.pack_start(sep,    False, False, 0)
        return wrap

    def _build_appearance_section(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        label = Gtk.Label(label='APPEARANCE')
        label.get_style_context().add_class('settings-section-label')
        label.set_halign(Gtk.Align.START)
        box.pack_start(label, False, False, 0)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        card.get_style_context().add_class('settings-card')
        card.set_border_width(12)

        card.pack_start(self._form_label('Theme'), False, False, 0)
        theme_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        self._theme_combo = Gtk.ComboBoxText()
        families = style_module.get_families()
        current_theme = self._config.get('theme', style_module.DEFAULT_THEME)

        for f in families:
            self._theme_combo.append(f['label'], f['label'])

        self._theme_combo.set_active_id(
            style_module.get_theme(current_theme)['label_family'])
        self._theme_combo.set_hexpand(True)
        self._theme_combo.connect('changed', self._on_theme_family_changed)
        theme_row.pack_start(self._theme_combo, True, True, 0)

        current_variant = style_module.get_theme(current_theme)['variant']
        self._dark_btn  = Gtk.RadioButton.new_with_label(None, '● Dark')
        self._light_btn = Gtk.RadioButton.new_with_label_from_widget(
            self._dark_btn, '☀ Light')
        self._dark_btn.get_style_context().add_class('form-label')
        self._light_btn.get_style_context().add_class('form-label')

        if current_variant == 'light':
            self._light_btn.set_active(True)
        else:
            self._dark_btn.set_active(True)

        self._dark_btn.connect('toggled', self._on_variant_toggled)
        theme_row.pack_start(self._dark_btn,  False, False, 0)
        theme_row.pack_start(self._light_btn, False, False, 0)
        card.pack_start(theme_row, False, False, 0)

        card.pack_start(self._form_label('Font Size'), False, False, 0)
        font_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        current_font = self._config.get('font_size', style_module.DEFAULT_FONT)

        for value, display in [('small', 'Small'), ('medium', 'Medium'), ('large', 'Large')]:
            btn = Gtk.Button(label=display)
            btn.get_style_context().add_class('width-btn')
            btn.set_relief(Gtk.ReliefStyle.NONE)
            if value == current_font:
                btn.get_style_context().add_class('active')
            btn.connect('clicked', self._on_font_clicked, value)
            self._font_buttons[value] = btn
            font_row.pack_start(btn, True, True, 0)

        card.pack_start(font_row, False, False, 0)
        box.pack_start(card, False, False, 0)
        return box

    def _on_theme_family_changed(self, combo):
        self._apply_theme_selection()

    def _on_variant_toggled(self, btn):
        self._apply_theme_selection()

    def _apply_theme_selection(self):
        family_label = self._theme_combo.get_active_id()
        if not family_label:
            return
        variant = 'light' if self._light_btn.get_active() else 'dark'
        for theme_id, theme in style_module.THEMES.items():
            if theme['label_family'] == family_label and theme['variant'] == variant:
                self._config = cfg_module.set_theme(self._config, theme_id)
                self._refresh_css()
                self._on_config_changed(self._config)
                break

    def _on_font_clicked(self, btn, value):
        for v, b in self._font_buttons.items():
            ctx = b.get_style_context()
            if v == value:
                ctx.add_class('active')
            else:
                ctx.remove_class('active')
        self._config = cfg_module.set_font_size(self._config, value)
        self._refresh_css()
        self._on_config_changed(self._config)

    # ── Layout section ────────────────────────────────────────────────────────

    def _build_layout_section(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        label = Gtk.Label(label='LAYOUT')
        label.get_style_context().add_class('settings-section-label')
        label.set_halign(Gtk.Align.START)
        box.pack_start(label, False, False, 0)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        card.get_style_context().add_class('settings-card')
        card.set_border_width(12)

        # Panel width
        card.pack_start(self._form_label('Panel Width'), False, False, 0)
        width_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        current_width = self._config.get('width', 'medium')
        self._width_buttons = {}
        for value, display in [('narrow', 'Narrow'), ('medium', 'Medium'), ('wide', 'Wide')]:
            btn = Gtk.Button(label=display)
            btn.get_style_context().add_class('width-btn')
            btn.set_relief(Gtk.ReliefStyle.NONE)
            if value == current_width:
                btn.get_style_context().add_class('active')
            btn.connect('clicked', self._on_width_clicked, value)
            self._width_buttons[value] = btn
            width_row.pack_start(btn, True, True, 0)
        card.pack_start(width_row, False, False, 0)

        # Panel position
        card.pack_start(self._form_label('Panel Side'), False, False, 0)
        position_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        current_position = self._config.get('position', 'right')
        for value, display in [('left', 'Left'), ('right', 'Right')]:
            btn = Gtk.Button(label=display)
            btn.get_style_context().add_class('width-btn')
            btn.set_relief(Gtk.ReliefStyle.NONE)
            if value == current_position:
                btn.get_style_context().add_class('active')
            btn.connect('clicked', self._on_position_clicked, value)
            self._position_buttons[value] = btn
            position_row.pack_start(btn, True, True, 0)
        card.pack_start(position_row, False, False, 0)

        # Strip position
        card.pack_start(self._form_label('Tab Strip Side'), False, False, 0)
        strip_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        current_strip = self._config.get('strip', 'left')
        for value, display in [('left', 'Left'), ('right', 'Right')]:
            btn = Gtk.Button(label=display)
            btn.get_style_context().add_class('width-btn')
            btn.set_relief(Gtk.ReliefStyle.NONE)
            if value == current_strip:
                btn.get_style_context().add_class('active')
            btn.connect('clicked', self._on_strip_clicked, value)
            self._strip_buttons[value] = btn
            strip_row.pack_start(btn, True, True, 0)
        card.pack_start(strip_row, False, False, 0)

        box.pack_start(card, False, False, 0)
        return box

    def _on_width_clicked(self, btn, value):
        for v, b in self._width_buttons.items():
            ctx = b.get_style_context()
            if v == value:
                ctx.add_class('active')
            else:
                ctx.remove_class('active')
        self._config = cfg_module.set_width(self._config, value)
        self._on_config_changed(self._config)

    def _on_position_clicked(self, btn, value):
        for v, b in self._position_buttons.items():
            ctx = b.get_style_context()
            if v == value:
                ctx.add_class('active')
            else:
                ctx.remove_class('active')
        self._config = cfg_module.set_position(self._config, value)
        self._on_config_changed(self._config)

    def _on_strip_clicked(self, btn, value):
        for v, b in self._strip_buttons.items():
            ctx = b.get_style_context()
            if v == value:
                ctx.add_class('active')
            else:
                ctx.remove_class('active')
        self._config = cfg_module.set_strip(self._config, value)
        self._on_config_changed(self._config)

    # ── Startup ───────────────────────────────────────────────────────────────

    def _build_startup_section(self) -> Gtk.Widget:
        import autostart

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        label = Gtk.Label(label='STARTUP')
        label.get_style_context().add_class('settings-section-label')
        label.set_halign(Gtk.Align.START)
        box.pack_start(label, False, False, 0)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row.get_style_context().add_class('settings-card')
        row.set_border_width(10)

        lbl = Gtk.Label(label='Start automatically on login')
        lbl.get_style_context().add_class('form-label')
        lbl.set_halign(Gtk.Align.START)
        lbl.set_hexpand(True)
        row.pack_start(lbl, True, True, 0)

        toggle = Gtk.Switch()
        toggle.set_active(autostart.is_autostart_enabled())
        toggle.set_valign(Gtk.Align.CENTER)
        toggle.connect('notify::active', self._on_autostart_toggled)
        row.pack_end(toggle, False, False, 0)

        box.pack_start(row, False, False, 0)
        return box

    def _on_autostart_toggled(self, switch, _):
        import autostart
        if switch.get_active():
            autostart.enable_autostart()
        else:
            autostart.disable_autostart()

    # ── Tabs list ─────────────────────────────────────────────────────────────

    def _build_tabs_section(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        label = Gtk.Label(label='TABS')
        label.get_style_context().add_class('settings-section-label')
        label.set_halign(Gtk.Align.START)
        box.pack_start(label, False, False, 0)

        self._tabs_list_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self._rebuild_tabs_list()
        box.pack_start(self._tabs_list_box, False, False, 0)

        return box

    def _rebuild_tabs_list(self):
        for child in self._tabs_list_box.get_children():
            self._tabs_list_box.remove(child)

        tabs = self._config.get('tabs', [])
        for i, tab in enumerate(tabs):
            row = self._build_tab_row(tab, i, len(tabs))
            self._tabs_list_box.pack_start(row, False, False, 0)

        self._tabs_list_box.show_all()

    def _build_tab_row(self, tab: dict, idx: int, total: int) -> Gtk.Widget:
        is_divider  = tab.get('type') == 'divider'
        is_document = tab.get('type') == 'document'

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        row.get_style_context().add_class('tab-row')
        if is_divider:
            row.get_style_context().add_class('divider-tab-row')

        if is_divider:
            icon_name = 'list-remove-symbolic'
        elif is_document:
            icon_name = 'x-office-document-symbolic'
        else:
            icon_name = tab.get('icon', 'text-x-generic-symbolic')

        icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.SMALL_TOOLBAR)
        icon.set_margin_start(6)
        row.pack_start(icon, False, False, 0)

        lbl_text = f"── {tab.get('label', '')} ──" if is_divider \
            else tab.get('label', '')
        lbl = Gtk.Label(label=lbl_text)
        lbl.set_halign(Gtk.Align.START)
        lbl.set_hexpand(True)
        lbl.get_style_context().add_class('form-label')
        lbl.set_margin_start(4)
        row.pack_start(lbl, True, True, 0)

        up_btn = Gtk.Button()
        up_btn.get_style_context().add_class('tab-row-btn')
        up_btn.set_relief(Gtk.ReliefStyle.NONE)
        up_btn.add(Gtk.Image.new_from_icon_name(
            'go-up-symbolic', Gtk.IconSize.SMALL_TOOLBAR))
        up_btn.set_sensitive(idx > 0)
        up_btn.connect('clicked', self._on_move_up, idx)
        row.pack_end(up_btn, False, False, 0)

        down_btn = Gtk.Button()
        down_btn.get_style_context().add_class('tab-row-btn')
        down_btn.set_relief(Gtk.ReliefStyle.NONE)
        down_btn.add(Gtk.Image.new_from_icon_name(
            'go-down-symbolic', Gtk.IconSize.SMALL_TOOLBAR))
        down_btn.set_sensitive(idx < total - 1)
        down_btn.connect('clicked', self._on_move_down, idx)
        row.pack_end(down_btn, False, False, 0)

        del_btn = Gtk.Button()
        del_btn.get_style_context().add_class('tab-row-btn')
        del_btn.get_style_context().add_class('delete')
        del_btn.set_relief(Gtk.ReliefStyle.NONE)
        del_btn.add(Gtk.Image.new_from_icon_name(
            'edit-delete-symbolic', Gtk.IconSize.SMALL_TOOLBAR))
        del_btn.connect('clicked', self._on_delete_tab, tab['id'])
        row.pack_end(del_btn, False, False, 0)

        return row

    def _on_move_up(self, btn, idx):
        tabs = self._config.get('tabs', [])
        if idx > 0:
            tabs[idx], tabs[idx - 1] = tabs[idx - 1], tabs[idx]
            self._config['tabs'] = tabs
            cfg_module.save(self._config)
            self._on_config_changed(self._config)
            self._rebuild_tabs_list()

    def _on_move_down(self, btn, idx):
        tabs = self._config.get('tabs', [])
        if idx < len(tabs) - 1:
            tabs[idx], tabs[idx + 1] = tabs[idx + 1], tabs[idx]
            self._config['tabs'] = tabs
            cfg_module.save(self._config)
            self._on_config_changed(self._config)
            self._rebuild_tabs_list()

    def _on_delete_tab(self, btn, tab_id):
        self._config = cfg_module.remove_tab(self._config, tab_id)
        self._on_config_changed(self._config)
        self._rebuild_tabs_list()

    # ── Add tab ───────────────────────────────────────────────────────────────

    def _build_add_section(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        label = Gtk.Label(label='ADD TAB')
        label.get_style_context().add_class('settings-section-label')
        label.set_halign(Gtk.Align.START)
        box.pack_start(label, False, False, 0)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        card.get_style_context().add_class('settings-card')
        card.set_border_width(12)

        card.pack_start(self._form_label('Label'), False, False, 0)
        self._label_entry = Gtk.Entry()
        self._label_entry.get_style_context().add_class('form-entry')
        self._label_entry.set_placeholder_text('e.g. Gemini, Portainer, Downloads')
        card.pack_start(self._label_entry, False, False, 0)

        card.pack_start(self._form_label('Type'), False, False, 0)
        type_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self._type_web      = Gtk.RadioButton.new_with_label(None, 'Web / URL')
        self._type_file     = Gtk.RadioButton.new_with_label_from_widget(
            self._type_web, 'File Browser')
        self._type_custom   = Gtk.RadioButton.new_with_label_from_widget(
            self._type_web, 'Plugin')
        self._type_document = Gtk.RadioButton.new_with_label_from_widget(
            self._type_web, 'Document')
        self._type_app = Gtk.RadioButton.new_with_label_from_widget(
            self._type_web, 'Application')
        for rb in [self._type_web, self._type_file, self._type_custom,
                   self._type_document, self._type_app]:
            rb.get_style_context().add_class('form-label')
            rb.connect('toggled', self._on_type_toggled)
            type_box.pack_start(rb, False, False, 0)
        card.pack_start(type_box, False, False, 0)

        self._url_label = self._form_label('URL')
        card.pack_start(self._url_label, False, False, 0)
        self._url_entry = Gtk.Entry()
        self._url_entry.get_style_context().add_class('form-entry')
        self._url_entry.set_placeholder_text('https://...')
        card.pack_start(self._url_entry, False, False, 0)

        self._plugin_label = self._form_label('Plugin')
        self._plugin_label.hide()
        card.pack_start(self._plugin_label, False, False, 0)

        self._plugin_combo = Gtk.ComboBoxText()
        self._plugin_combo.hide()
        try:
            from tabs.custom import available_plugins
            plugins = available_plugins()
            if plugins:
                for plugin in plugins:
                    self._plugin_combo.append(plugin['id'], plugin['label'])
                self._plugin_combo.set_active(0)
            else:
                self._plugin_combo.append('none', '— no plugins installed —')
                self._plugin_combo.set_active(0)
        except Exception:
            self._plugin_combo.append('none', '— no plugins installed —')
            self._plugin_combo.set_active(0)
        card.pack_start(self._plugin_combo, False, False, 0)

        self._doc_label = self._form_label('File Path')
        self._doc_label.hide()
        card.pack_start(self._doc_label, False, False, 0)

        self._doc_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self._doc_row.hide()

        self._doc_entry = Gtk.Entry()
        self._doc_entry.get_style_context().add_class('form-entry')
        self._doc_entry.set_placeholder_text('/home/user/document.pdf')
        self._doc_entry.set_hexpand(True)
        self._doc_row.pack_start(self._doc_entry, True, True, 0)

        browse_btn = Gtk.Button(label='Browse')
        browse_btn.get_style_context().add_class('width-btn')
        browse_btn.set_relief(Gtk.ReliefStyle.NONE)
        browse_btn.connect('clicked', self._on_browse_document)
        self._doc_row.pack_start(browse_btn, False, False, 0)
        card.pack_start(self._doc_row, False, False, 0)

        self._app_label = self._form_label('Application')
        self._app_label.hide()
        card.pack_start(self._app_label, False, False, 0)

        self._app_picker_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self._app_picker_box.hide()

        self._app_search_entry = Gtk.SearchEntry()
        self._app_search_entry.set_placeholder_text('Search applications...')
        self._app_search_entry.connect(
            'search-changed', self._on_app_search_changed)
        self._app_picker_box.pack_start(
            self._app_search_entry, False, False, 0)

        app_scroll = Gtk.ScrolledWindow()
        app_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        app_scroll.set_min_content_height(180)
        app_scroll.set_max_content_height(180)

        self._app_listbox = Gtk.ListBox()
        self._app_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._app_listbox.set_filter_func(self._app_filter_func)
        self._app_listbox.connect('row-selected', self._on_app_row_selected)

        self._selected_app_id = None
        try:
            from tabs.app_discovery import list_apps
            self._available_apps = list_apps()
        except Exception:
            self._available_apps = []

        for app in self._available_apps:
            row = Gtk.ListBoxRow()
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            row_box.set_margin_start(6)
            row_box.set_margin_end(6)
            row_box.set_margin_top(4)
            row_box.set_margin_bottom(4)
            row_icon = Gtk.Image.new_from_icon_name(
                app['icon'], Gtk.IconSize.SMALL_TOOLBAR)
            row_box.pack_start(row_icon, False, False, 0)
            row_lbl = Gtk.Label(label=app['name'])
            row_lbl.set_halign(Gtk.Align.START)
            row_box.pack_start(row_lbl, True, True, 0)
            row.add(row_box)
            row.app_id   = app['id']
            row.app_name = app['name']
            self._app_listbox.add(row)

        app_scroll.add(self._app_listbox)
        self._app_picker_box.pack_start(app_scroll, True, True, 0)
        card.pack_start(self._app_picker_box, False, False, 0)

        self._icon_label = self._form_label('Icon')
        card.pack_start(self._icon_label, False, False, 0)
        self._icon_picker_widget = self._build_icon_picker()
        card.pack_start(self._icon_picker_widget, False, False, 0)

        if self._presets:
            sep = Gtk.Separator()
            sep.get_style_context().add_class('preset-divider')
            sep.set_margin_top(4)
            sep.set_margin_bottom(4)
            card.pack_start(sep, False, False, 0)

            preset_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            preset_lbl = self._form_label('Load from preset')
            preset_lbl.set_hexpand(True)
            preset_row.pack_start(preset_lbl, True, True, 0)

            self._preset_combo = Gtk.ComboBoxText()
            self._preset_combo.append('none', '— select —')
            for preset in self._presets:
                self._preset_combo.append(preset['preset_id'], preset['label'])
            self._preset_combo.set_active_id('none')
            self._preset_combo.connect('changed', self._on_preset_selected)
            preset_row.pack_end(self._preset_combo, False, False, 0)
            card.pack_start(preset_row, False, False, 0)

        add_btn = Gtk.Button(label='Add Tab')
        add_btn.get_style_context().add_class('add-btn')
        add_btn.set_relief(Gtk.ReliefStyle.NONE)
        add_btn.connect('clicked', self._on_add_tab)
        card.pack_start(add_btn, False, False, 0)

        box.pack_start(card, False, False, 0)
        return box

    def _on_browse_document(self, btn):
        dialog = Gtk.FileChooserDialog(
            title='Select Document',
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,   Gtk.ResponseType.OK,
        )

        f_pdf = Gtk.FileFilter()
        f_pdf.set_name('PDF files')
        f_pdf.add_mime_type('application/pdf')
        dialog.add_filter(f_pdf)

        f_all = Gtk.FileFilter()
        f_all.set_name('All files')
        f_all.add_pattern('*')
        dialog.add_filter(f_all)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self._doc_entry.set_text(dialog.get_filename())
        dialog.destroy()

    # ── Add divider ───────────────────────────────────────────────────────────

    def _build_divider_section(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        label = Gtk.Label(label='ADD DIVIDER')
        label.get_style_context().add_class('settings-section-label')
        label.set_halign(Gtk.Align.START)
        box.pack_start(label, False, False, 0)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        card.get_style_context().add_class('settings-card')
        card.set_border_width(12)

        card.pack_start(self._form_label('Label'), False, False, 0)
        self._divider_entry = Gtk.Entry()
        self._divider_entry.get_style_context().add_class('form-entry')
        self._divider_entry.set_placeholder_text('e.g. Work, Files, AI')
        card.pack_start(self._divider_entry, False, False, 0)

        add_btn = Gtk.Button(label='Add Divider')
        add_btn.get_style_context().add_class('add-btn')
        add_btn.set_relief(Gtk.ReliefStyle.NONE)
        add_btn.connect('clicked', self._on_add_divider)
        card.pack_start(add_btn, False, False, 0)

        box.pack_start(card, False, False, 0)
        return box

    def _on_add_divider(self, btn):
        label = self._divider_entry.get_text().strip()
        if not label:
            return
        tab = {
            'id':    str(uuid.uuid4()),
            'type':  'divider',
            'label': label,
        }
        self._config = cfg_module.add_tab(self._config, tab)
        self._on_config_changed(self._config)
        self._rebuild_tabs_list()
        self._divider_entry.set_text('')

    def _form_label(self, text: str) -> Gtk.Label:
        lbl = Gtk.Label(label=text)
        lbl.get_style_context().add_class('form-label')
        lbl.set_halign(Gtk.Align.START)
        return lbl

    def _on_type_toggled(self, btn):
        is_web      = self._type_web.get_active()
        is_file     = self._type_file.get_active()
        is_custom   = self._type_custom.get_active()
        is_document = self._type_document.get_active()
        is_app      = self._type_app.get_active()

        if is_web:
            self._url_label.set_text('URL')
            self._url_entry.set_placeholder_text('https://...')
            self._url_label.show()
            self._url_entry.show()
        elif is_file:
            self._url_label.set_text('Folder Path')
            self._url_entry.set_placeholder_text('/home/user/documents')
            self._url_label.show()
            self._url_entry.show()
        else:
            self._url_label.hide()
            self._url_entry.hide()

        if is_custom:
            self._plugin_label.show()
            self._plugin_combo.show()
        else:
            self._plugin_label.hide()
            self._plugin_combo.hide()

        if is_document:
            self._doc_label.show()
            self._doc_row.show()
        else:
            self._doc_label.hide()
            self._doc_row.hide()

        if is_app:
            self._app_label.show()
            self._app_picker_box.show()
        else:
            self._app_label.hide()
            self._app_picker_box.hide()

        self._icon_label.show()
        self._icon_picker_widget.show()

    def _on_app_search_changed(self, entry):
        self._app_listbox.invalidate_filter()

    def _app_filter_func(self, row):
        query = self._app_search_entry.get_text().strip().lower()
        if not query:
            return True
        return query in row.app_name.lower()

    def _on_app_row_selected(self, listbox, row):
        if row is None:
            return
        self._selected_app_id = row.app_id
        if not self._label_entry.get_text().strip():
            self._label_entry.set_text(row.app_name)

    def _on_preset_selected(self, combo):
        preset_id = combo.get_active_id()
        if preset_id == 'none':
            return
        for preset in self._presets:
            if preset['preset_id'] == preset_id:
                self._label_entry.set_text(preset.get('label', ''))
                self._url_entry.set_text(preset.get('url', ''))
                if preset.get('type') == 'web':
                    self._type_web.set_active(True)
                else:
                    self._type_file.set_active(True)
                icon = preset.get('icon', ICON_OPTIONS[0][0])
                if icon in self._icon_buttons:
                    self._select_icon(icon)
                break

    def _build_icon_picker(self) -> Gtk.Widget:
        flow = Gtk.FlowBox()
        flow.set_max_children_per_line(6)
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_row_spacing(6)
        flow.set_column_spacing(6)

        self._icon_buttons = {}
        for icon_name, tooltip in ICON_OPTIONS:
            btn = Gtk.Button()
            btn.get_style_context().add_class('icon-btn')
            btn.set_relief(Gtk.ReliefStyle.NONE)
            btn.set_tooltip_text(tooltip)
            btn.add(Gtk.Image.new_from_icon_name(
                icon_name, Gtk.IconSize.LARGE_TOOLBAR))
            btn.connect('clicked', self._on_icon_selected, icon_name)
            self._icon_buttons[icon_name] = btn
            flow.add(btn)

        self._select_icon(ICON_OPTIONS[0][0])
        return flow

    def _on_icon_selected(self, btn, icon_name):
        self._select_icon(icon_name)

    def _select_icon(self, icon_name: str):
        self._selected_icon = icon_name
        for name, btn in self._icon_buttons.items():
            ctx = btn.get_style_context()
            if name == icon_name:
                ctx.add_class('selected')
            else:
                ctx.remove_class('selected')

    def _on_add_tab(self, btn):
        label       = self._label_entry.get_text().strip()
        is_custom   = self._type_custom.get_active()
        is_document = self._type_document.get_active()
        is_app      = self._type_app.get_active()

        if is_app:
            app_id = self._selected_app_id
            if not label or not app_id:
                return
            icon = self._selected_icon
            for app in self._available_apps:
                if app['id'] == app_id:
                    icon = app['icon']
                    break
            tab = {
                'id':     str(uuid.uuid4()),
                'type':   'app',
                'app_id': app_id,
                'label':  label,
                'icon':   icon,
            }
        elif is_document:
            path = self._doc_entry.get_text().strip()
            if not label or not path:
                return
            tab = {
                'id':    str(uuid.uuid4()),
                'type':  'document',
                'label': label,
                'path':  path,
                'icon':  self._selected_icon,
            }
        elif is_custom:
            plugin_id = self._plugin_combo.get_active_id()
            if not label or not plugin_id or plugin_id == 'none':
                return
            tab = {
                'id':        str(uuid.uuid4()),
                'type':      'custom',
                'custom_id': plugin_id,
                'label':     label,
                'icon':      self._selected_icon,
            }
        else:
            url = self._url_entry.get_text().strip()
            if not label or not url:
                return
            tab_type = 'web' if self._type_web.get_active() else 'files'
            tab = {
                'id':    str(uuid.uuid4()),
                'type':  tab_type,
                'label': label,
                'url' if tab_type == 'web' else 'path': url,
                'icon':  self._selected_icon,
            }

        self._config = cfg_module.add_tab(self._config, tab)
        self._on_config_changed(self._config)
        self._rebuild_tabs_list()
