import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
import uuid
import config as cfg_module

# Curated icon options for the picker
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

CSS = """
.settings-root {
    background-color: #0f1117;
}
.settings-section-label {
    color: #4a5568;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.08em;
}
.settings-card {
    background-color: #1a1d2e;
    border-radius: 8px;
    border: 1px solid #2d3748;
}
.width-btn {
    background: transparent;
    border: 1px solid #2d3748;
    border-radius: 6px;
    color: #a0aec0;
    padding: 6px 12px;
    font-size: 12px;
}
.width-btn:hover {
    background-color: #2d3748;
    color: #e2e8f0;
}
.width-btn.active {
    background-color: #6366f1;
    border-color: #6366f1;
    color: #ffffff;
}
.tab-row {
    background-color: #1a1d2e;
    border-radius: 6px;
    border: 1px solid #2d3748;
    padding: 4px;
}
.tab-row-btn {
    background: transparent;
    border: none;
    border-radius: 4px;
    color: #4a5568;
    padding: 4px;
    min-width: 26px;
    min-height: 26px;
}
.tab-row-btn:hover {
    background-color: #2d3748;
    color: #e2e8f0;
}
.tab-row-btn.delete:hover {
    background-color: #742a2a;
    color: #fc8181;
}
.add-btn {
    background-color: #6366f1;
    border: none;
    border-radius: 6px;
    color: #ffffff;
    padding: 8px 16px;
    font-size: 12px;
    font-weight: 500;
}
.add-btn:hover {
    background-color: #818cf8;
}
.form-entry {
    background-color: #1a1d2e;
    border: 1px solid #2d3748;
    border-radius: 6px;
    color: #e2e8f0;
    padding: 6px 10px;
    font-size: 12px;
}
.form-entry:focus {
    border-color: #6366f1;
}
.form-label {
    color: #a0aec0;
    font-size: 11px;
}
.icon-btn {
    background: transparent;
    border: 1px solid #2d3748;
    border-radius: 6px;
    color: #4a5568;
    padding: 6px;
    min-width: 36px;
    min-height: 36px;
}
.icon-btn:hover {
    background-color: #2d3748;
    color: #a0aec0;
}
.icon-btn.selected {
    border-color: #6366f1;
    background-color: rgba(99, 102, 241, 0.13);
    color: #6366f1;
}
.back-btn {
    background: transparent;
    border: none;
    border-radius: 4px;
    color: #4a5568;
    padding: 4px 8px;
    font-size: 12px;
}
.back-btn:hover {
    background-color: #1a1d2e;
    color: #a0aec0;
}
.divider {
    background-color: #1e2130;
}
.preset-divider {
    background-color: #2d3748;
}
switch {
    background-color: #2d3748;
    border-radius: 14px;
    border: none;
}
switch:checked {
    background-color: #6366f1;
}
switch slider {
    background-color: #e2e8f0;
    border-radius: 12px;
    min-width: 24px;
    min-height: 24px;
}
"""


class SettingsPanel:
    def __init__(self, config: dict, on_back, on_config_changed):
        self._config            = config
        self._on_back           = on_back
        self._on_config_changed = on_config_changed
        self._selected_icon     = ICON_OPTIONS[0][0]
        self._width_buttons     = {}
        self._presets           = []

        self._apply_css()
        self._load_presets()
        self.widget = self._build()

    # ── CSS ───────────────────────────────────────────────────────────────────

    def _apply_css(self):
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    # ── Presets ───────────────────────────────────────────────────────────────

    def _load_presets(self):
        try:
            from tabs.presets import load_all
            self._presets = load_all()
        except Exception as e:
            print(f"Warning: could not load presets: {e}")
            self._presets = []

    # ── Build ─────────────────────────────────────────────────────────────────

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

        content.pack_start(self._build_width_section(),   False, False, 0)
        content.pack_start(self._build_startup_section(), False, False, 0)
        content.pack_start(self._build_tabs_section(),    False, False, 0)
        content.pack_start(self._build_add_section(),     False, False, 0)

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

    # ── Width section ─────────────────────────────────────────────────────────

    def _build_width_section(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        label = Gtk.Label(label='PANEL WIDTH')
        label.get_style_context().add_class('settings-section-label')
        label.set_halign(Gtk.Align.START)
        box.pack_start(label, False, False, 0)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        current = self._config.get('width', 'half')

        for value, display in [('quarter', 'Quarter'), ('half', 'Half'), ('full', 'Full')]:
            btn = Gtk.Button(label=display)
            btn.get_style_context().add_class('width-btn')
            btn.set_relief(Gtk.ReliefStyle.NONE)
            if value == current:
                btn.get_style_context().add_class('active')
            btn.connect('clicked', self._on_width_clicked, value)
            self._width_buttons[value] = btn
            btn_box.pack_start(btn, True, True, 0)

        box.pack_start(btn_box, False, False, 0)
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

    # ── Startup section ───────────────────────────────────────────────────────

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

    # ── Tabs section ──────────────────────────────────────────────────────────

    def _build_tabs_section(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        label = Gtk.Label(label='TABS')
        label.get_style_context().add_class('settings-section-label')
        label.set_halign(Gtk.Align.START)
        box.pack_start(label, False, False, 0)

        self._tabs_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
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
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        row.get_style_context().add_class('tab-row')

        icon = Gtk.Image.new_from_icon_name(
            tab.get('icon', 'text-x-generic-symbolic'),
            Gtk.IconSize.SMALL_TOOLBAR,
        )
        icon.set_margin_start(6)
        row.pack_start(icon, False, False, 0)

        lbl = Gtk.Label(label=tab.get('label', ''))
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

    # ── Add tab section ───────────────────────────────────────────────────────

    def _build_add_section(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        label = Gtk.Label(label='ADD TAB')
        label.get_style_context().add_class('settings-section-label')
        label.set_halign(Gtk.Align.START)
        box.pack_start(label, False, False, 0)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        card.get_style_context().add_class('settings-card')
        card.set_border_width(12)

        # Label field
        card.pack_start(self._form_label('Label'), False, False, 0)
        self._label_entry = Gtk.Entry()
        self._label_entry.get_style_context().add_class('form-entry')
        self._label_entry.set_placeholder_text('e.g. Gemini, Portainer, Downloads')
        card.pack_start(self._label_entry, False, False, 0)

        # Type selector
        card.pack_start(self._form_label('Type'), False, False, 0)
        type_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self._type_web    = Gtk.RadioButton.new_with_label(None, 'Web / URL')
        self._type_file   = Gtk.RadioButton.new_with_label_from_widget(
            self._type_web, 'File Browser')
        self._type_custom = Gtk.RadioButton.new_with_label_from_widget(
            self._type_web, 'Plugin')
        self._type_web.get_style_context().add_class('form-label')
        self._type_file.get_style_context().add_class('form-label')
        self._type_custom.get_style_context().add_class('form-label')
        self._type_web.connect('toggled',    self._on_type_toggled)
        self._type_file.connect('toggled',   self._on_type_toggled)
        self._type_custom.connect('toggled', self._on_type_toggled)
        type_box.pack_start(self._type_web,    False, False, 0)
        type_box.pack_start(self._type_file,   False, False, 0)
        type_box.pack_start(self._type_custom, False, False, 0)
        card.pack_start(type_box, False, False, 0)

        # URL / path field
        self._url_label = self._form_label('URL')
        card.pack_start(self._url_label, False, False, 0)
        self._url_entry = Gtk.Entry()
        self._url_entry.get_style_context().add_class('form-entry')
        self._url_entry.set_placeholder_text('https://...')
        card.pack_start(self._url_entry, False, False, 0)

        # Plugin selector (shown only when Plugin is selected)
        self._plugin_label = self._form_label('Plugin')
        self._plugin_label.set_no_show_all(True)
        self._plugin_label.hide()
        card.pack_start(self._plugin_label, False, False, 0)

        self._plugin_combo = Gtk.ComboBoxText()
        self._plugin_combo.set_no_show_all(True)
        self._plugin_combo.hide()
        self._load_plugin_combo()
        card.pack_start(self._plugin_combo, False, False, 0)

        # Icon picker
        card.pack_start(self._form_label('Icon'), False, False, 0)
        card.pack_start(self._build_icon_picker(), False, False, 0)

        # Divider + preset dropdown
        if self._presets:
            sep = Gtk.Separator()
            sep.get_style_context().add_class('preset-divider')
            sep.set_margin_top(4)
            sep.set_margin_bottom(4)
            card.pack_start(sep, False, False, 0)

            preset_row = Gtk.Box(
                orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            preset_lbl = self._form_label('Load from preset')
            preset_lbl.set_hexpand(True)
            preset_row.pack_start(preset_lbl, True, True, 0)

            self._preset_combo = Gtk.ComboBoxText()
            self._preset_combo.append('none', '— select —')
            for preset in self._presets:
                self._preset_combo.append(
                    preset['preset_id'], preset['label'])
            self._preset_combo.set_active_id('none')
            self._preset_combo.connect('changed', self._on_preset_selected)
            preset_row.pack_end(self._preset_combo, False, False, 0)
            card.pack_start(preset_row, False, False, 0)

        # Add button
        add_btn = Gtk.Button(label='Add Tab')
        add_btn.get_style_context().add_class('add-btn')
        add_btn.set_relief(Gtk.ReliefStyle.NONE)
        add_btn.connect('clicked', self._on_add_tab)
        card.pack_start(add_btn, False, False, 0)

        box.pack_start(card, False, False, 0)
        return box

    def _load_plugin_combo(self):
        self._plugin_combo.remove_all()
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

    def _form_label(self, text: str) -> Gtk.Label:
        lbl = Gtk.Label(label=text)
        lbl.get_style_context().add_class('form-label')
        lbl.set_halign(Gtk.Align.START)
        return lbl

    def _on_type_toggled(self, btn):
        is_web    = self._type_web.get_active()
        is_file   = self._type_file.get_active()
        is_custom = self._type_custom.get_active()

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
        elif is_custom:
            self._url_label.hide()
            self._url_entry.hide()

        if is_custom:
            self._plugin_label.show()
            self._plugin_combo.show()
        else:
            self._plugin_label.hide()
            self._plugin_combo.hide()

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
        label     = self._label_entry.get_text().strip()
        is_custom = self._type_custom.get_active()

        if is_custom:
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

        # Clear the form
        self._label_entry.set_text('')
        self._url_entry.set_text('')
        self._select_icon(ICON_OPTIONS[0][0])
        if hasattr(self, '_preset_combo'):
            self._preset_combo.set_active_id('none')
