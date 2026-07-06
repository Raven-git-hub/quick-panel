import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, Gdk, GLib, Gio, GdkPixbuf
import os
import shutil
from pathlib import Path

# Drag and drop target types
DRAG_TARGETS = [
    Gtk.TargetEntry.new('text/uri-list', 0, 0),
]

# Image extensions that get thumbnails
IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg'}

# Icon sizes for small/large toggle
ICON_SIZE_SMALL = 24
ICON_SIZE_LARGE = 48
THUMB_SIZE_SMALL = 32
THUMB_SIZE_LARGE = 64


def build(tab: dict) -> Gtk.Widget:
    root_path = tab.get('path', str(Path.home()))
    browser = FileBrowser(root_path=root_path)
    return browser.widget


class FileBrowser:
    def __init__(self, root_path: str):
        self._root            = Path(root_path)
        self._current         = self._root
        self._clipboard_files = []
        self._clipboard_mode  = None
        self._view_mode       = 'tile'   # 'tile' or 'list'
        self._icon_size       = 'large'  # 'small' or 'large'
        self._sort_key        = 'name_asc'
        self._search_text     = ''

        self.widget = self._build()
        self._load_directory(self._current)

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self) -> Gtk.Widget:
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        root.set_hexpand(True)
        root.set_vexpand(True)

        root.pack_start(self._build_toolbar(), False, False, 0)

        # Breadcrumb
        self._breadcrumb_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        self._breadcrumb_box.set_margin_start(8)
        self._breadcrumb_box.set_margin_end(8)
        self._breadcrumb_box.set_margin_top(4)
        self._breadcrumb_box.set_margin_bottom(4)
        root.pack_start(self._breadcrumb_box, False, False, 0)

        sep = Gtk.Separator()
        root.pack_start(sep, False, False, 0)

        # Offline label
        self._offline_label = Gtk.Label(
            label='⚠ Folder not accessible.\nCheck that the path is mounted and reachable.')
        self._offline_label.set_justify(Gtk.Justification.CENTER)
        self._offline_label.set_valign(Gtk.Align.CENTER)
        self._offline_label.set_vexpand(True)

        # ── List store ────────────────────────────────────────────────────────
        # Columns: 0=name, 1=icon_name, 2=type, 3=mtime, 4=size, 5=pixbuf
        self._store = Gtk.ListStore(str, str, str, float, int, GdkPixbuf.Pixbuf)

        # Sort model
        self._sort_model = Gtk.TreeModelSort(model=self._store)
        self._apply_sort()

        # Filter model
        self._filter_model = self._sort_model.filter_new()
        self._filter_model.set_visible_func(self._filter_func)

        # ── Icon view (tile mode) ─────────────────────────────────────────────
        self._icon_view = Gtk.IconView()
        self._icon_view.set_model(self._filter_model)
        self._icon_view.set_selection_mode(Gtk.SelectionMode.MULTIPLE)
        self._icon_view.set_item_width(90)
        self._icon_view.set_column_spacing(4)
        self._icon_view.set_row_spacing(4)
        self._icon_view.set_margin(8)

        self._icon_view.clear()

        self._icon_pixbuf_renderer = Gtk.CellRendererPixbuf()
        self._icon_pixbuf_renderer.set_property('stock-size', Gtk.IconSize.DIALOG)
        self._icon_view.pack_start(self._icon_pixbuf_renderer, False)
        self._icon_view.add_attribute(
            self._icon_pixbuf_renderer, 'pixbuf', 5)

        self._icon_name_renderer = Gtk.CellRendererPixbuf()
        self._icon_name_renderer.set_property('stock-size', Gtk.IconSize.DIALOG)
        self._icon_view.pack_start(self._icon_name_renderer, False)
        self._icon_view.add_attribute(
            self._icon_name_renderer, 'icon-name', 1)

        text_renderer = Gtk.CellRendererText()
        text_renderer.set_property('alignment', 1)
        text_renderer.set_property('wrap-mode', 2)
        text_renderer.set_property('wrap-width', 80)
        text_renderer.set_property('ellipsize', 3)
        self._icon_view.pack_start(text_renderer, False)
        self._icon_view.add_attribute(text_renderer, 'text', 0)

        self._icon_view.connect('item-activated', self._on_item_activated_icon)
        self._icon_view.connect('button-press-event', self._on_button_press)

        self._icon_view.enable_model_drag_source(
            Gdk.ModifierType.BUTTON1_MASK, DRAG_TARGETS, Gdk.DragAction.COPY)
        self._icon_view.connect('drag-data-get', self._on_drag_data_get_icon)
        self._icon_view.enable_model_drag_dest(
            DRAG_TARGETS, Gdk.DragAction.COPY)
        self._icon_view.connect('drag-data-received', self._on_drag_data_received)

        # ── Tree view (list mode) ─────────────────────────────────────────────
        self._tree_view = Gtk.TreeView(model=self._filter_model)
        self._tree_view.set_headers_visible(True)
        self._tree_view.set_enable_search(False)
        self._tree_view.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)

        # Icon column
        icon_col = Gtk.TreeViewColumn('')
        icon_cell = Gtk.CellRendererPixbuf()
        icon_cell.set_property('stock-size', Gtk.IconSize.SMALL_TOOLBAR)
        icon_col.pack_start(icon_cell, False)
        icon_col.add_attribute(icon_cell, 'pixbuf', 5)
        icon_col.add_attribute(icon_cell, 'icon-name', 1)
        icon_col.set_fixed_width(32)
        self._tree_view.append_column(icon_col)

        # Name column
        name_col = Gtk.TreeViewColumn('Name')
        name_cell = Gtk.CellRendererText()
        name_cell.set_property('ellipsize', 3)
        name_col.pack_start(name_cell, True)
        name_col.add_attribute(name_cell, 'text', 0)
        name_col.set_expand(True)
        name_col.set_sort_column_id(0)
        self._tree_view.append_column(name_col)

        # Type column
        type_col = Gtk.TreeViewColumn('Type')
        type_cell = Gtk.CellRendererText()
        type_col.pack_start(type_cell, False)
        type_col.add_attribute(type_cell, 'text', 2)
        type_col.set_fixed_width(50)
        self._tree_view.append_column(type_col)

        self._tree_view.connect('row-activated', self._on_item_activated_tree)
        self._tree_view.connect('button-press-event', self._on_button_press)

        self._tree_view.enable_model_drag_source(
            Gdk.ModifierType.BUTTON1_MASK, DRAG_TARGETS, Gdk.DragAction.COPY)
        self._tree_view.connect('drag-data-get', self._on_drag_data_get_tree)
        self._tree_view.enable_model_drag_dest(
            DRAG_TARGETS, Gdk.DragAction.COPY)
        self._tree_view.connect('drag-data-received', self._on_drag_data_received)

        # Scrolled windows
        self._icon_scroll = Gtk.ScrolledWindow()
        self._icon_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self._icon_scroll.set_vexpand(True)
        self._icon_scroll.add(self._icon_view)

        self._tree_scroll = Gtk.ScrolledWindow()
        self._tree_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self._tree_scroll.set_vexpand(True)
        self._tree_scroll.add(self._tree_view)

        # View stack
        self._view_stack = Gtk.Stack()
        self._view_stack.add_named(self._icon_scroll, 'tile')
        self._view_stack.add_named(self._tree_scroll, 'list')
        self._view_stack.add_named(self._offline_label, 'offline')
        self._view_stack.set_visible_child_name('tile')

        root.pack_start(self._view_stack, True, True, 0)
        return root

    def _build_toolbar(self) -> Gtk.Widget:
        bar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Top row — navigation + actions
        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        top.set_margin_start(8)
        top.set_margin_end(8)
        top.set_margin_top(6)
        top.set_margin_bottom(4)

        # Back
        self._back_btn = Gtk.Button()
        self._back_btn.add(Gtk.Image.new_from_icon_name(
            'go-previous-symbolic', Gtk.IconSize.SMALL_TOOLBAR))
        self._back_btn.set_relief(Gtk.ReliefStyle.NONE)
        self._back_btn.set_tooltip_text('Go up')
        self._back_btn.set_sensitive(False)
        self._back_btn.connect('clicked', self._on_go_up)
        top.pack_start(self._back_btn, False, False, 0)

        # Refresh
        refresh_btn = Gtk.Button()
        refresh_btn.add(Gtk.Image.new_from_icon_name(
            'view-refresh-symbolic', Gtk.IconSize.SMALL_TOOLBAR))
        refresh_btn.set_relief(Gtk.ReliefStyle.NONE)
        refresh_btn.set_tooltip_text('Refresh')
        refresh_btn.connect('clicked', lambda _: self._load_directory(self._current))
        top.pack_start(refresh_btn, False, False, 0)

        # New folder
        new_folder_btn = Gtk.Button()
        new_folder_btn.add(Gtk.Image.new_from_icon_name(
            'folder-new-symbolic', Gtk.IconSize.SMALL_TOOLBAR))
        new_folder_btn.set_relief(Gtk.ReliefStyle.NONE)
        new_folder_btn.set_tooltip_text('New folder')
        new_folder_btn.connect('clicked', self._on_new_folder)
        top.pack_start(new_folder_btn, False, False, 0)

        top.pack_start(Gtk.Separator(
            orientation=Gtk.Orientation.VERTICAL), False, False, 4)

        # View toggle — tile
        self._tile_btn = Gtk.Button()
        self._tile_btn.add(Gtk.Image.new_from_icon_name(
            'view-grid-symbolic', Gtk.IconSize.SMALL_TOOLBAR))
        self._tile_btn.set_relief(Gtk.ReliefStyle.NONE)
        self._tile_btn.set_tooltip_text('Tile view')
        self._tile_btn.connect('clicked', lambda _: self._set_view_mode('tile'))
        top.pack_start(self._tile_btn, False, False, 0)

        # View toggle — list
        self._list_btn = Gtk.Button()
        self._list_btn.add(Gtk.Image.new_from_icon_name(
            'view-list-symbolic', Gtk.IconSize.SMALL_TOOLBAR))
        self._list_btn.set_relief(Gtk.ReliefStyle.NONE)
        self._list_btn.set_tooltip_text('List view')
        self._list_btn.connect('clicked', lambda _: self._set_view_mode('list'))
        top.pack_start(self._list_btn, False, False, 0)

        top.pack_start(Gtk.Separator(
            orientation=Gtk.Orientation.VERTICAL), False, False, 4)

        # Size toggle
        self._size_btn = Gtk.Button()
        self._size_btn.add(Gtk.Image.new_from_icon_name(
            'zoom-in-symbolic', Gtk.IconSize.SMALL_TOOLBAR))
        self._size_btn.set_relief(Gtk.ReliefStyle.NONE)
        self._size_btn.set_tooltip_text('Toggle icon size')
        self._size_btn.connect('clicked', self._on_toggle_size)
        top.pack_start(self._size_btn, False, False, 0)

        top.pack_start(Gtk.Separator(
            orientation=Gtk.Orientation.VERTICAL), False, False, 4)

        # Sort dropdown
        self._sort_combo = Gtk.ComboBoxText()
        self._sort_combo.append('name_asc',  'Name A→Z')
        self._sort_combo.append('name_desc', 'Name Z→A')
        self._sort_combo.append('date_desc', 'Newest first')
        self._sort_combo.append('date_asc',  'Oldest first')
        self._sort_combo.append('size_desc', 'Largest first')
        self._sort_combo.append('size_asc',  'Smallest first')
        self._sort_combo.set_active_id('name_asc')
        self._sort_combo.connect('changed', self._on_sort_changed)
        top.pack_start(self._sort_combo, False, False, 0)

        bar.pack_start(top, False, False, 0)

        # Bottom row — search
        search_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        search_row.set_margin_start(8)
        search_row.set_margin_end(8)
        search_row.set_margin_bottom(6)

        search_icon = Gtk.Image.new_from_icon_name(
            'system-search-symbolic', Gtk.IconSize.SMALL_TOOLBAR)
        search_row.pack_start(search_icon, False, False, 0)

        self._search_entry = Gtk.SearchEntry()
        self._search_entry.set_placeholder_text('Search files...')
        self._search_entry.set_hexpand(True)
        self._search_entry.connect('search-changed', self._on_search_changed)
        search_row.pack_start(self._search_entry, True, True, 0)

        bar.pack_start(search_row, False, False, 0)

        return bar

    # ── Directory loading ─────────────────────────────────────────────────────

    def _load_directory(self, path: Path):
        if not path.exists() or not path.is_dir():
            self._view_stack.set_visible_child_name('offline')
            return

        self._view_stack.set_visible_child_name(self._view_mode)
        self._current = path
        self._store.clear()
        self._update_breadcrumb()
        self._back_btn.set_sensitive(self._current != self._root)

        try:
            entries = sorted(path.iterdir(),
                             key=lambda e: (not e.is_dir(), e.name.lower()))

            for entry in entries:
                if entry.name.startswith('.'):
                    continue
                icon_name  = self._get_icon(entry)
                entry_type = 'dir' if entry.is_dir() else 'file'
                try:
                    stat  = entry.stat()
                    mtime = stat.st_mtime
                    size  = stat.st_size if entry.is_file() else 0
                except OSError:
                    mtime = 0.0
                    size  = 0

                self._store.append([
                    entry.name,
                    icon_name,
                    entry_type,
                    mtime,
                    size,
                    None,  # pixbuf — loaded async for images
                ])

            # Load thumbnails async
            self._load_thumbnails_async(path)

        except PermissionError:
            self._view_stack.set_visible_child_name('offline')

    def _load_thumbnails_async(self, path: Path):
        """Load image thumbnails in the background without blocking the UI."""
        thumb_size = THUMB_SIZE_LARGE if self._icon_size == 'large' else THUMB_SIZE_SMALL

        def load_next(entries, idx):
            if idx >= len(entries):
                return False
            entry, row_ref = entries[idx]
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(
                    str(entry), thumb_size, thumb_size)
                tree_path = row_ref.get_path()
                if tree_path:
                    it = self._store.get_iter(tree_path)
                    if it:
                        self._store.set_value(it, 5, pixbuf)
                        # Clear icon name so only pixbuf shows
                        self._store.set_value(it, 1, '')
            except Exception:
                pass
            GLib.idle_add(load_next, entries, idx + 1)
            return False

        # Collect image entries with row references
        image_entries = []
        it = self._store.get_iter_first()
        while it:
            name = self._store.get_value(it, 0)
            entry = path / name
            if entry.suffix.lower() in IMAGE_EXTS:
                row_ref = Gtk.TreeRowReference.new(
                    self._store, self._store.get_path(it))
                image_entries.append((entry, row_ref))
            it = self._store.iter_next(it)

        if image_entries:
            GLib.idle_add(load_next, image_entries, 0)

    def _get_icon(self, path: Path) -> str:
        if path.is_dir():
            return 'folder'
        ext = path.suffix.lower()
        icon_map = {
            '.pdf':  'application-pdf',
            '.png':  'image-x-generic',
            '.jpg':  'image-x-generic',
            '.jpeg': 'image-x-generic',
            '.gif':  'image-x-generic',
            '.webp': 'image-x-generic',
            '.svg':  'image-x-generic',
            '.mp3':  'audio-x-generic',
            '.flac': 'audio-x-generic',
            '.wav':  'audio-x-generic',
            '.mp4':  'video-x-generic',
            '.mkv':  'video-x-generic',
            '.txt':  'text-x-generic',
            '.md':   'text-x-generic',
            '.py':   'text-x-script',
            '.sh':   'text-x-script',
            '.zip':  'package-x-generic',
            '.tar':  'package-x-generic',
            '.gz':   'package-x-generic',
        }
        return icon_map.get(ext, 'text-x-generic')

    def _update_breadcrumb(self):
        for child in self._breadcrumb_box.get_children():
            self._breadcrumb_box.remove(child)

        try:
            rel   = self._current.relative_to(self._root)
            parts = [self._root.name] + list(rel.parts)
            paths = [self._root] + [
                self._root.joinpath(*rel.parts[:i+1])
                for i in range(len(rel.parts))
            ]
        except ValueError:
            parts = [self._root.name]
            paths = [self._root]

        for i, (part, path) in enumerate(zip(parts, paths)):
            btn = Gtk.Button(label=part)
            btn.set_relief(Gtk.ReliefStyle.NONE)
            btn.get_style_context().add_class('back-btn')
            btn.connect('clicked', lambda _, p=path: self._load_directory(p))
            self._breadcrumb_box.pack_start(btn, False, False, 0)

            if i < len(parts) - 1:
                sep = Gtk.Label(label='›')
                sep.get_style_context().add_class('form-label')
                self._breadcrumb_box.pack_start(sep, False, False, 0)

        self._breadcrumb_box.show_all()

    # ── View mode ─────────────────────────────────────────────────────────────

    def _set_view_mode(self, mode: str):
        self._view_mode = mode
        self._view_stack.set_visible_child_name(mode)

    def _on_toggle_size(self, btn):
        if self._icon_size == 'large':
            self._icon_size = 'small'
            self._icon_pixbuf_renderer.set_property('stock-size', Gtk.IconSize.SMALL_TOOLBAR)
            self._icon_name_renderer.set_property('stock-size', Gtk.IconSize.SMALL_TOOLBAR)
            self._icon_view.set_item_width(60)
        else:
            self._icon_size = 'large'
            self._icon_pixbuf_renderer.set_property('stock-size', Gtk.IconSize.DIALOG)
            self._icon_name_renderer.set_property('stock-size', Gtk.IconSize.DIALOG)
            self._icon_view.set_item_width(90)
        # Reload thumbnails at new size
        self._load_directory(self._current)

    # ── Sort ──────────────────────────────────────────────────────────────────

    def _on_sort_changed(self, combo):
        self._sort_key = combo.get_active_id()
        self._apply_sort()

    def _apply_sort(self):
        sort_map = {
            'name_asc':  (0, Gtk.SortType.ASCENDING),
            'name_desc': (0, Gtk.SortType.DESCENDING),
            'date_desc': (3, Gtk.SortType.DESCENDING),
            'date_asc':  (3, Gtk.SortType.ASCENDING),
            'size_desc': (4, Gtk.SortType.DESCENDING),
            'size_asc':  (4, Gtk.SortType.ASCENDING),
        }
        col, order = sort_map.get(self._sort_key, (0, Gtk.SortType.ASCENDING))
        self._sort_model.set_sort_column_id(col, order)

    # ── Search ────────────────────────────────────────────────────────────────

    def _on_search_changed(self, entry):
        self._search_text = entry.get_text().lower()
        self._filter_model.refilter()

    def _filter_func(self, model, it, data):
        if not self._search_text:
            return True
        name = model.get_value(it, 0) or ''
        return self._search_text in name.lower()

    # ── Navigation ────────────────────────────────────────────────────────────

    def _on_item_activated_icon(self, icon_view, path):
        it        = self._filter_model.get_iter(path)
        name      = self._filter_model.get_value(it, 0)
        item_type = self._filter_model.get_value(it, 2)
        full_path = self._current / name

        if item_type == 'dir':
            self._load_directory(full_path)
        else:
            Gio.AppInfo.launch_default_for_uri(full_path.as_uri(), None)

    def _on_item_activated_tree(self, tree_view, path, column):
        it        = self._filter_model.get_iter(path)
        name      = self._filter_model.get_value(it, 0)
        item_type = self._filter_model.get_value(it, 2)
        full_path = self._current / name

        if item_type == 'dir':
            self._load_directory(full_path)
        else:
            Gio.AppInfo.launch_default_for_uri(full_path.as_uri(), None)

    def _on_go_up(self, btn):
        if self._current != self._root:
            self._load_directory(self._current.parent)

    # ── Context menu ──────────────────────────────────────────────────────────

    def _on_button_press(self, widget, event):
        if event.button == 3:
            self._show_context_menu(event)
            return True
        return False

    def _show_context_menu(self, event):
        selected = self._get_selected_paths()
        menu     = Gtk.Menu()

        if selected:
            open_item = Gtk.MenuItem(label='Open')
            open_item.connect('activate', lambda _: self._open_selected(selected))
            menu.append(open_item)

            menu.append(Gtk.SeparatorMenuItem())

            copy_item = Gtk.MenuItem(label='Copy')
            copy_item.connect('activate', lambda _: self._copy_to_clipboard(selected))
            menu.append(copy_item)

            cut_item = Gtk.MenuItem(label='Cut')
            cut_item.connect('activate', lambda _: self._cut_to_clipboard(selected))
            menu.append(cut_item)

            menu.append(Gtk.SeparatorMenuItem())

            if len(selected) == 1:
                rename_item = Gtk.MenuItem(label='Rename')
                rename_item.connect('activate', lambda _: self._rename_file(selected[0]))
                menu.append(rename_item)

            delete_item = Gtk.MenuItem(label='Delete')
            delete_item.connect('activate', lambda _: self._delete_files(selected))
            menu.append(delete_item)

            menu.append(Gtk.SeparatorMenuItem())

        paste_item = Gtk.MenuItem(label='Paste')
        paste_item.set_sensitive(bool(self._clipboard_files))
        paste_item.connect('activate', lambda _: self._paste_files())
        menu.append(paste_item)

        new_folder_item = Gtk.MenuItem(label='New Folder')
        new_folder_item.connect('activate', self._on_new_folder)
        menu.append(new_folder_item)

        menu.show_all()
        menu.popup_at_pointer(event)

    def _get_selected_paths(self) -> list:
        if self._view_mode == 'tile':
            selected = self._icon_view.get_selected_items()
            paths = []
            for tree_path in selected:
                it   = self._filter_model.get_iter(tree_path)
                name = self._filter_model.get_value(it, 0)
                paths.append(self._current / name)
            return paths
        else:
            selection = self._tree_view.get_selection()
            model, rows = selection.get_selected_rows()
            paths = []
            for tree_path in rows:
                it   = model.get_iter(tree_path)
                name = model.get_value(it, 0)
                paths.append(self._current / name)
            return paths

    # ── File operations ───────────────────────────────────────────────────────

    def _open_selected(self, paths: list):
        for path in paths:
            if path.is_dir():
                self._load_directory(path)
            else:
                Gio.AppInfo.launch_default_for_uri(path.as_uri(), None)

    def _copy_to_clipboard(self, paths: list):
        self._clipboard_files = paths
        self._clipboard_mode  = 'copy'

    def _cut_to_clipboard(self, paths: list):
        self._clipboard_files = paths
        self._clipboard_mode  = 'cut'

    def _paste_files(self):
        if not self._clipboard_files:
            return
        for src in self._clipboard_files:
            dest = self._current / src.name
            try:
                if src.is_dir():
                    shutil.copytree(str(src), str(dest))
                else:
                    shutil.copy2(str(src), str(dest))
                if self._clipboard_mode == 'cut':
                    if src.is_dir():
                        shutil.rmtree(str(src))
                    else:
                        src.unlink()
            except Exception as e:
                self._show_error(f"Could not paste {src.name}: {e}")
        if self._clipboard_mode == 'cut':
            self._clipboard_files = []
            self._clipboard_mode  = None
        self._load_directory(self._current)

    def _delete_files(self, paths: list):
        dialog = Gtk.MessageDialog(
            transient_for=self.widget.get_toplevel(),
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text=f'Delete {len(paths)} item(s)?',
        )
        dialog.format_secondary_text('This cannot be undone.')
        response = dialog.run()
        dialog.destroy()

        if response == Gtk.ResponseType.OK:
            for path in paths:
                try:
                    if path.is_dir():
                        shutil.rmtree(str(path))
                    else:
                        path.unlink()
                except Exception as e:
                    self._show_error(f"Could not delete {path.name}: {e}")
            self._load_directory(self._current)

    def _rename_file(self, path: Path):
        dialog = Gtk.Dialog(
            title='Rename',
            transient_for=self.widget.get_toplevel(),
            flags=0,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK,     Gtk.ResponseType.OK,
        )
        entry = Gtk.Entry()
        entry.set_text(path.name)
        entry.select_region(0, len(path.stem))
        dialog.get_content_area().pack_start(entry, True, True, 8)
        dialog.show_all()
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            new_name = entry.get_text().strip()
            if new_name and new_name != path.name:
                try:
                    path.rename(self._current / new_name)
                    self._load_directory(self._current)
                except Exception as e:
                    self._show_error(f"Could not rename: {e}")
        dialog.destroy()

    def _on_new_folder(self, *_):
        dialog = Gtk.Dialog(
            title='New Folder',
            transient_for=self.widget.get_toplevel(),
            flags=0,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK,     Gtk.ResponseType.OK,
        )
        entry = Gtk.Entry()
        entry.set_placeholder_text('Folder name')
        dialog.get_content_area().pack_start(entry, True, True, 8)
        dialog.show_all()
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            name = entry.get_text().strip()
            if name:
                try:
                    (self._current / name).mkdir()
                    self._load_directory(self._current)
                except Exception as e:
                    self._show_error(f"Could not create folder: {e}")
        dialog.destroy()

    # ── Drag out ──────────────────────────────────────────────────────────────

    def _on_drag_data_get_icon(self, widget, context, data, info, time):
        selected = self._get_selected_paths()
        uris     = [p.as_uri() for p in selected]
        data.set_uris(uris)

    def _on_drag_data_get_tree(self, widget, context, data, info, time):
        selected = self._get_selected_paths()
        uris     = [p.as_uri() for p in selected]
        data.set_uris(uris)

    # ── Drag in ───────────────────────────────────────────────────────────────

    def _on_drag_data_received(self, widget, context, x, y, data, info, time):
        uris = data.get_uris()
        for uri in uris:
            src  = Path(Gio.File.new_for_uri(uri).get_path())
            dest = self._current / src.name
            try:
                if src.is_dir():
                    shutil.copytree(str(src), str(dest))
                else:
                    shutil.copy2(str(src), str(dest))
            except Exception as e:
                self._show_error(f"Could not copy {src.name}: {e}")
        self._load_directory(self._current)
        Gtk.drag_finish(context, True, False, time)

    # ── Error dialog ──────────────────────────────────────────────────────────

    def _show_error(self, message: str):
        dialog = Gtk.MessageDialog(
            transient_for=self.widget.get_toplevel(),
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text='Error',
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
