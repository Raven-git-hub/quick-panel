#!/usr/bin/env python3
"""
Quick Panel — entry point.
Initialises the panel, tray icon, and optional keyboard shortcut.
"""

import sys
import os

# Ensure src/ is on the path so all imports resolve correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import config
from panel import Panel
from tray import TrayIcon


def main():
    cfg = config.load()

    panel = Panel(cfg)
    tray  = TrayIcon(on_toggle=panel.toggle, on_quit=Gtk.main_quit)

    # Optional global shortcut: Ctrl+`  (X11 only — keybinder has no effect
    # under Wayland)
    hotkey_bound = False
    try:
        gi.require_version('Keybinder', '3.0')
        from gi.repository import Keybinder
        Keybinder.init()
        Keybinder.bind('<Ctrl>grave', lambda key, _: panel.toggle())
        hotkey_bound = True
    except Exception:
        pass

    if not cfg.get('tabs'):
        # First run — no tabs configured, open straight to settings
        panel.show()
        panel._open_settings()
    elif not tray.available:
        # No working tray icon on this system. Starting hidden would make
        # the app unreachable (unless the hotkey happens to work), so show
        # the panel — the user can hide it with Esc or the close button.
        print("Quick Panel: no system tray host detected "
              "(is the AppIndicator extension enabled?). "
              "Showing panel on startup so it stays reachable."
              + (" Ctrl+` toggles it." if hotkey_bound else ""))
        panel.show()

    Gtk.main()


if __name__ == '__main__':
    main()
