"""
App discovery — lists installed desktop applications for the App tab
picker. Uses Gio.DesktopAppInfo, which reads the standard XDG
application directories the same way your app launcher does.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gio


def list_apps() -> list:
    """
    Returns a sorted list of dicts: {id, name, icon, exec}
    Skips NoDisplay/Hidden entries and duplicates.
    """
    apps = []
    seen_ids = set()

    for app_info in Gio.AppInfo.get_all():
        if not isinstance(app_info, Gio.DesktopAppInfo):
            continue
        if not app_info.should_show():
            continue

        app_id = app_info.get_id() or app_info.get_name()
        if not app_id or app_id in seen_ids:
            continue
        seen_ids.add(app_id)

        icon = app_info.get_icon()
        icon_name = icon.to_string() if icon else 'application-x-executable'

        apps.append({
            'id':   app_id,
            'name': app_info.get_display_name() or app_info.get_name(),
            'icon': icon_name,
        })

    return sorted(apps, key=lambda a: a['name'].lower())
