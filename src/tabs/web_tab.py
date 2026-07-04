import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, WebKit2


def build(tab: dict) -> Gtk.Widget:
    url = tab.get('url', 'about:blank')

    settings = WebKit2.Settings()
    settings.set_enable_javascript(True)
    settings.set_enable_media(True)
    settings.set_enable_webgl(True)
    settings.set_enable_media_stream(True)
    settings.set_javascript_can_access_clipboard(True)
    settings.set_hardware_acceleration_policy(
        WebKit2.HardwareAccelerationPolicy.ALWAYS
    )
    settings.set_user_agent(
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    )

    # Per-tab persistent session storage
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

    # Handle new window requests — open in same view instead of spawning
    # a new window (which would segfault with no handler)
    wv.connect('create', _on_create_window)

    # Handle navigation policy — keep everything in the same view
    wv.connect('decide-policy', _on_decide_policy)

    return wv


def _on_create_window(wv, action):
    """
    Called when the page tries to open a new window/tab.
    We load it in the same WebView instead of creating a new one.
    """
    nav_action = action.get_navigation_action()
    req = nav_action.get_request()
    uri = req.get_uri()
    if uri and uri != 'about:blank':
        wv.load_uri(uri)
    return wv


def _on_decide_policy(wv, decision, decision_type):
    """
    Allow all navigation within the same view.
    """
    if decision_type == WebKit2.PolicyDecisionType.NEW_WINDOW_ACTION:
        nav = decision.get_navigation_action()
        req = nav.get_request()
        uri = req.get_uri()
        if uri:
            wv.load_uri(uri)
        decision.ignore()
        return True
    decision.use()
    return False


def reload(widget: Gtk.Widget):
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
