import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, Gdk, WebKit2
from urllib.parse import urlparse


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
    wv.connect('load-failed-with-tls-errors', _on_tls_error)

    wv._parent_domain = urlparse(url).netloc
    wv._tab_ctx       = ctx
    wv._tab_settings  = settings

    wv.connect('create', lambda wv, action: _on_create_window(wv, action))
    wv.connect('decide-policy', _on_decide_policy)

    return wv


def _on_create_window(parent_wv, action):
    print("DEBUG: create signal fired")
    nav_action = action.get_navigation_action()
    req        = nav_action.get_request()
    uri        = req.get_uri()
    print(f"DEBUG: create uri={uri}")

    if not uri or uri == 'about:blank':
        return parent_wv

    parent_domain = getattr(parent_wv, '_parent_domain', '')
    popup_domain  = urlparse(uri).netloc

    if popup_domain == parent_domain:
        parent_wv.load_uri(uri)
        return parent_wv

    _open_oauth_popup(parent_wv, uri, parent_domain)
    return parent_wv


def _open_oauth_popup(parent_wv, uri: str, parent_domain: str):
    screen  = Gdk.Screen.get_default()
    monitor = screen.get_primary_monitor()
    geo     = screen.get_monitor_workarea(monitor)
    width   = min(600, int(geo.width * 0.5))
    height  = min(700, int(geo.height * 0.8))

    win = Gtk.Window()
    win.set_title('Login')
    win.set_default_size(width, height)
    win.set_position(Gtk.WindowPosition.CENTER)
    win.set_keep_above(True)

    ctx      = parent_wv._tab_ctx
    settings = parent_wv._tab_settings

    popup_wv = WebKit2.WebView.new_with_context(ctx)
    popup_wv.set_settings(settings)
    popup_wv.load_uri(uri)
    popup_wv.set_hexpand(True)
    popup_wv.set_vexpand(True)

    def _on_load_changed(wv, event):
        if event != WebKit2.LoadEvent.COMMITTED:
            return
        current_uri    = wv.get_uri() or ''
        current_domain = urlparse(current_uri).netloc
        print(f"DEBUG popup load: uri={current_uri} domain={current_domain} parent={parent_domain}")
        if current_domain and parent_domain and current_domain == parent_domain:
            parent_wv.load_uri(current_uri)
            win.destroy()

    popup_wv.connect('load-changed', _on_load_changed)

    def _on_popup_create(wv, action):
        nav     = action.get_navigation_action()
        req     = nav.get_request()
        new_uri = req.get_uri()
        print(f"DEBUG popup create: uri={new_uri}")
        if new_uri and new_uri != 'about:blank':
            wv.load_uri(new_uri)
        return wv

    popup_wv.connect('create', _on_popup_create)
    popup_wv.connect('load-failed-with-tls-errors', _on_tls_error)

    header = Gtk.HeaderBar()
    header.set_show_close_button(True)
    header.set_title('Login')
    win.set_titlebar(header)

    win.add(popup_wv)
    win.show_all()


def _on_tls_error(wv, failing_uri, certificate, errors):
    try:
        host = failing_uri.split('/')[2].split(':')[0]
        ctx  = wv.get_context()
        ctx.allow_tls_certificate_for_host(certificate, host)
        wv.load_uri(failing_uri)
    except Exception as e:
        print(f"TLS error handler failed: {e}")
    return True


def _on_decide_policy(wv, decision, decision_type):
    try:
        uri = decision.get_navigation_action().get_request().get_uri()
    except Exception:
        uri = 'unknown'
    print(f"DEBUG: decide-policy type={decision_type} uri={uri}")

    if decision_type == WebKit2.PolicyDecisionType.NEW_WINDOW_ACTION:
        nav = decision.get_navigation_action()
        req = nav.get_request()
        uri = req.get_uri()
        if uri:
            print(f"DEBUG: NEW_WINDOW_ACTION uri={uri}")
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
