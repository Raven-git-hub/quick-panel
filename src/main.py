#!/usr/bin/env python3
"""
Quick Panel — entry point.
Initialises the panel, tray icon, and optional keyboard shortcut.
"""

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

    # Optional global shortcut: Ctrl+`
    try:
        gi.require_version('Keybinder', '3.0')
        from gi.repository import Keybinder
        Keybinder.init()
        Keybinder.bind('<Ctrl>grave', lambda key, _: panel.toggle())
    except Exception:
        pass  # keybinder3 not installed — tray icon still works

    Gtk.main()


if __name__ == '__main__':
    main()
