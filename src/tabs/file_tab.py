import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Gio
import os
import shutil
from pathlib import Path


# Drag and drop target types
DRAG_TARGETS = [
    Gtk.TargetEntry.new('text/uri-list', 0, 0),
]


def build(tab: dict) -> Gtk.Widget:
    root_path = tab.get('path', str(Path.home()))
    browser = FileBrowser(root_path=root_path)
    return browser.widget


class FileBrowser:
    def __init__(self, root_path: str):
        self._root   = Path(root_path)
        self._current = self._root
        self._clipboard_files = []
        self._clipboard_mode  = None  # 'copy' or 'cut'

        self.widget = self._build()
        self._load_directory(self._current)

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self) -> Gtk.Widget:
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        root.set_hexpand(True)
        root.set_vexpand(True)

        # Toolbar
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

        # Not connected label (hidden by default)
        self._offline_label = Gtk.Label(
            label='⚠ Folder not accessible.\nCheck that the path is mounted and reachable.')
        self._offline_label.set_justify(Gtk.Justification.CENTER)
        self._offline_label.set_valign(Gtk.Align.CENTER)
        self._offline_label.set_vexpand(True)
        self._offline_label.set_no_show_all(True)

        # File icon view
        self._store = Gtk.ListStore(str, str, str)  # name, icon_name, type
        self._icon_view = Gtk.IconView()
        self._icon_view.set_model(self._store)
        self._icon_view.set_text_column(0)
        self._icon_view.set_pixbuf_column(-1)  # we use icon name, not pixbuf
        self._icon_view.set_item_width(80)
        self._icon_view.set_selection_mode(Gtk.SelectionMode.MULTIPLE)

        # Use a cell renderer for the icon
        self._icon_view.clear()
        icon_renderer = Gtk.CellRendererPixbuf()
        icon_renderer.set_property('stock-size', Gtk.IconSize.DIALOG)
        self._icon_view.pack_start(icon_renderer, False)
        self._icon_view.add_attribute(icon_renderer, 'icon-name', 1)

        text_renderer = Gtk.CellRendererText()
        text_renderer.set_property('alignment', 1)  # center
        text_renderer.set_property('wrap-mode', 2)
        text_renderer.set_property('wrap-width', 80)
        text_renderer.set_property('ellipsize', 3)
        self._icon_view.pack_start(text_renderer, False)
        self._icon_view.add_attribute(text_renderer, 'text', 0)

        self._icon_view.connect('item-activated', self._on_item_activated)
        self._icon_view.connect('button-press-event', self._on_button_press)

        # Drag out (from panel)
        self._icon_view.enable_model_drag_source(
            Gdk.ModifierType.BUTTON1_MASK,
            DRAG_TARGETS,
            Gdk.DragAction.COPY,
        )
        self._icon_view.connect('drag-data-get', self._on_drag_data_get)

        # Drag in (to panel)
        self._icon_view.enable_model_drag_dest(
            DRAG_TARGETS,
            Gdk.DragAction.COPY,
        )
        self._icon_view.connect('drag-data-received', self._on_drag_data_received)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        scroll.add(self._icon_view)

        # Stack to switch between file view and offline message
        self._view_stack = Gtk.Stack()
        self._view_stack.add_named(scroll,               'files')
        self._view_stack.add_named(self._offline_label,  'offline')
        self._view_stack.set_visible_child_name('files')

        root.pack_start(self._view_stack, True, True, 0)
        return root

    def _build_toolbar(self) -> Gtk.Widget:
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        bar.set_margin_start(8)
        bar.set_margin_end(8)
        bar.set_margin_top(6)
        bar.set_margin_bottom(6)

        # Back button
        self._back_btn = Gtk.Button()
        self._back_btn.add(Gtk.Image.new_from_icon_name(
            'go-previous-symbolic', Gtk.IconSize.SMALL_TOOLBAR))
        self._back_btn.set_relief(Gtk.ReliefStyle.NONE)
        self._back_btn.set_tooltip_text('Go up')
        self._back_btn.set_sensitive(False)
        self._back_btn.connect('clicked', self._on_go_up)
        bar.pack_start(self._back_btn, False, False, 0)

        # Refresh button
        refresh_btn = Gtk.Button()
        refresh_btn.add(Gtk.Image.new_from_icon_name(
            'view-refresh-symbolic', Gtk.IconSize.SMALL_TOOLBAR))
        refresh_btn.set_relief(Gtk.ReliefStyle.NONE)
        refresh_btn.set_tooltip_text('Refresh')
        refresh_btn.connect('clicked', lambda _: self._load_directory(self._current))
        bar.pack_start(refresh_btn, False, False, 0)

        # New folder button
        new_folder_btn = Gtk.Button()
        new_folder_btn.add(Gtk.Image.new_from_icon_name(
            'folder-new-symbolic', Gtk.IconSize.SMALL_TOOLBAR))
        new_folder_btn.set_relief(Gtk.ReliefStyle.NONE)
        new_folder_btn.set_tooltip_text('New folder')
        new_folder_btn.connect('clicked', self._on_new_folder)
        bar.pack_start(new_folder_btn, False, False, 0)

        return bar

    # ── Directory loading ─────────────────────────────────────────────────────

    def _load_directory(self, path: Path):
        if not path.exists() or not path.is_dir():
            self._view_stack.set_visible_child_name('offline')
            return

        self._view_stack.set_visible_child_name('files')
        self._current = path
        self._store.clear()
        self._update_breadcrumb()
        self._back_btn.set_sensitive(self._current != self._root)

        try:
            entries = sorted(path.iterdir(), key=lambda e: (
                not e.is_dir(), e.name.lower()))

            for entry in entries:
                if entry.name.startswith('.'):
                    continue  # hide dotfiles
                icon_name = self._get_icon(entry)
                entry_type = 'dir' if entry.is_dir() else 'file'
                self._store.append([entry.name, icon_name, entry_type])

        except PermissionError:
            self._view_stack.set_visible_child_name('offline')

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

        # Build path parts relative to root
        try:
            rel = self._current.relative_to(self._root)
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

    # ── Navigation ────────────────────────────────────────────────────────────

    def _on_item_activated(self, icon_view, path):
        it = self._store.get_iter(path)
        name      = self._store.get_value(it, 0)
        item_type = self._store.get_value(it, 2)
        full_path = self._current / name

        if item_type == 'dir':
            self._load_directory(full_path)
        else:
            # Open with default system app
            Gio.AppInfo.launch_default_for_uri(
                full_path.as_uri(), None)

    def _on_go_up(self, btn):
        if self._current != self._root:
            self._load_directory(self._current.parent)

    # ── Context menu ──────────────────────────────────────────────────────────

    def _on_button_press(self, widget, event):
        if event.button == 3:  # right click
            self._show_context_menu(event)
            return True
        return False

    def _show_context_menu(self, event):
        selected = self._get_selected_paths()
        menu = Gtk.Menu()

        if selected:
            # Open
            open_item = Gtk.MenuItem(label='Open')
            open_item.connect('activate', lambda _: self._open_selected(selected))
            menu.append(open_item)

            menu.append(Gtk.SeparatorMenuItem())

            # Copy
            copy_item = Gtk.MenuItem(label='Copy')
            copy_item.connect('activate', lambda _: self._copy_to_clipboard(selected))
            menu.append(copy_item)

            # Cut
            cut_item = Gtk.MenuItem(label='Cut')
            cut_item.connect('activate', lambda _: self._cut_to_clipboard(selected))
            menu.append(cut_item)

            menu.append(Gtk.SeparatorMenuItem())

            # Rename (single file only)
            if len(selected) == 1:
                rename_item = Gtk.MenuItem(label='Rename')
                rename_item.connect('activate', lambda _: self._rename_file(selected[0]))
                menu.append(rename_item)

            # Delete
            delete_item = Gtk.MenuItem(label='Delete')
            delete_item.connect('activate', lambda _: self._delete_files(selected))
            menu.append(delete_item)

            menu.append(Gtk.SeparatorMenuItem())

        # Paste (always available if clipboard has files)
        paste_item = Gtk.MenuItem(label='Paste')
        paste_item.set_sensitive(bool(self._clipboard_files))
        paste_item.connect('activate', lambda _: self._paste_files())
        menu.append(paste_item)

        # New folder
        new_folder_item = Gtk.MenuItem(label='New Folder')
        new_folder_item.connect('activate', self._on_new_folder)
        menu.append(new_folder_item)

        menu.show_all()
        menu.popup_at_pointer(event)

    def _get_selected_paths(self) -> list:
        selected = self._icon_view.get_selected_items()
        paths = []
        for tree_path in selected:
            it = self._store.get_iter(tree_path)
            name = self._store.get_value(it, 0)
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
        # Confirm dialog
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

    def _on_drag_data_get(self, widget, context, data, info, time):
        selected = self._get_selected_paths()
        uris = [p.as_uri() for p in selected]
        data.set_uris(uris)

    # ── Drag in ───────────────────────────────────────────────────────────────

    def _on_drag_data_received(self, widget, context, x, y, data, info, time):
        uris = data.get_uris()
        for uri in uris:
            src = Path(Gio.File.new_for_uri(uri).get_path())
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
