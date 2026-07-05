import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, WebKit2
from pathlib import Path


def build(tab: dict) -> Gtk.Widget:
    path = tab.get('path', '')

    wv = WebKit2.WebView()
    wv.set_hexpand(True)
    wv.set_vexpand(True)

    if path and Path(path).exists():
        wv.load_uri(f"file://{path}")
    else:
        wv.load_html(
            "<html><body style='background:#0f1117;color:#4a5568;"
            "font-family:system-ui;display:flex;align-items:center;"
            "justify-content:center;height:100vh;margin:0;'>"
            "<p>File not found.<br>Check the path in Settings.</p>"
            "</body></html>",
            None
        )

    return wv
