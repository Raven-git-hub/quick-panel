import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, WebKit2
from pathlib import Path


def build(tab: dict) -> Gtk.Widget:
    path = tab.get('path', '')

    settings = WebKit2.Settings()
    settings.set_enable_javascript(False)
    settings.set_hardware_acceleration_policy(
        WebKit2.HardwareAccelerationPolicy.ALWAYS
    )

    ctx = WebKit2.WebContext.get_default()

    wv = WebKit2.WebView.new_with_context(ctx)
    wv.set_settings(settings)
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
