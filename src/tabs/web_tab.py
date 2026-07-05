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

    data_manager = WebKit2.WebsiteDataManager(
        base_data_directory=_data_dir(tab['id']),
        base_cache_directory=_cache_dir(tab['id']),
    )
    ctx = WebKit2.WebContext(website_data_manager=data_manager)

    cookie_manager = data_manager.get_cookie_manager()
    cookie_manager.set_persistent_storage(
        _cookie_file(tab['id']),
        WebKit2.CookiePersistentStorage.SQLITE,
    )
    cookie_manager.set_accept_policy(WebKit2.CookieAcceptPolicy.ALWAYS)

    wv = WebKit2.WebView.new_with_context(ctx)
    wv.set_settings(settings)
    wv.load_uri(url)
    wv.set_hexpand(True)
    wv.set_vexpand(True)
    wv.connect('create', _on_create_window)
    wv.connect('decide-policy', _on_decide_policy)
    wv.connect('load-failed-with-tls-errors', _on_tls_error)

    return wv


def _on_tls_error(wv, failing_uri, certificate, errors):
    """Accept self-signed certificates for local network hosts."""
    try:
        host = failing_uri.split('/')[2].split(':')[0]
        ctx  = wv.get_context()
        ctx.allow_tls_certificate_for_host(certificate, host)
        wv.load_uri(failing_uri)
    except Exception as e:
        print(f"TLS error handler failed: {e}")
    return True


def _on_create_window(wv, action):
    nav_action = action.get_navigation_action()
    req = nav_action.get_request()
    uri = req.get_uri()
    if uri and uri != 'about:blank':
        wv.load_uri(uri)
    return wv


def _on_decide_policy(wv, decision, decision_type):
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


def _cookie_file(tab_id: str) -> str:
    from pathlib import Path
    d = Path.home() / '.local' / 'share' / 'quick-panel' / 'tabs' / tab_id
    d.mkdir(parents=True, exist_ok=True)
    return str(d / 'cookies.db')
