import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, WebKit2


def build(tab: dict) -> Gtk.Widget:
    """
    Build a WebKit2 web view for a given tab config entry.
    Returns a Gtk.Widget ready to drop into the panel stack.
    """
    url = tab.get('url', 'about:blank')

    settings = WebKit2.Settings()
    settings.set_enable_javascript(True)
    settings.set_enable_media(True)
    settings.set_hardware_acceleration_policy(
        WebKit2.HardwareAccelerationPolicy.ALWAYS
    )
    # Spoof a real browser UA so sites don't serve degraded pages
    settings.set_user_agent(
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.0 Safari/605.1.15"
    )

    # Each tab gets its own cookie/session storage so logins persist
    data_manager = WebKit2.WebsiteDataManager(
        base_data_directory=_data_dir(tab['id']),
        base_cache_directory=_cache_dir(tab['id']),
    )
    ctx = WebKit2.WebContext(website_data_manager=data_manager)

    wv = WebKit2.WebView.new_with_context(ctx)
    wv.set_settings(settings)
    wv.load_uri(url)
    wv.set_hexpand(True)
    wv.set_vexpand(True)

    return wv


def reload(widget: Gtk.Widget):
    """Reload if the widget is a WebView."""
    if isinstance(widget, WebKit2.WebView):
        widget.reload()


def _data_dir(tab_id: str) -> str:
    from pathlib import Path
    d = Path.home() / '.local' / 'share' / 'quick-panel' / 'tabs' / tab_id
    d.mkdir(parents=True, exist_ok=True)
    return str(d)


def _cache_dir(tab_id: str) -> str:
    from pathlib import Path
    d = Path.home() / '.cache' / 'quick-panel' / 'tabs' / tab_id
    d.mkdir(parents=True, exist_ok=True)
    return str(d)
