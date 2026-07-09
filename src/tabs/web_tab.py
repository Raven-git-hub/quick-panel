"""
Web tab — WebKit2 WebView with per-tab isolated session storage.

Popup / OAuth handling:
  New-window requests (window.open, OAuth login popups) are handled via the
  'create' signal, returning a WebView built with new_with_related_view().
  Related views share the parent's web process and session, which gives the
  popup a working window.opener link back to the page that opened it — this
  is what Google / Microsoft / Apple button-based login flows need to
  complete (they postMessage the result back to the opener, then call
  window.close()).

  Do NOT intercept NEW_WINDOW_ACTION in a decide-policy handler: doing so
  suppresses the 'create' signal entirely and breaks these flows. (This was
  the previous behaviour and the main reason OAuth buttons appeared dead.)

  FedCM-only flows (e.g. Google One Tap) are still unsupported — WebKitGTK
  does not implement FedCM.

Per-site compatibility:
  Some sites need non-default WebKit settings. These are resolved in order:
    built-in defaults  <  DOMAIN_COMPAT match on the tab URL  <  explicit
    keys on the tab config dict ('user_agent', 'hardware_acceleration',
    'developer_tools' — hand-editable in config.json).
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, Gdk, WebKit2
from urllib.parse import urlparse
from pathlib import Path


# ── User agents ───────────────────────────────────────────────────────────────

UA_CHROME = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)
UA_SAFARI = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Safari/605.1.15"
)

# 'default' means: don't set a UA at all, use WebKit's native string.
UA_ALIASES = {
    'chrome':  UA_CHROME,
    'safari':  UA_SAFARI,
    'default': None,
}

# ── Per-domain compatibility table ────────────────────────────────────────────
# Matched against the netloc of the tab URL (exact host or any subdomain).
# Keys: user_agent (alias or raw string), hardware_acceleration
# ('always' | 'on-demand' | 'never'), developer_tools (bool).

DOMAIN_COMPAT = {
    # Proton runs browser-specific code paths and heavy WebCrypto (SRP) during
    # login. Present as Safari (we ARE a WebKit engine — the Chrome spoof is a
    # fingerprint mismatch), avoid forced hardware acceleration (known
    # WebKitGTK/Wayland DMA-BUF hangs), and enable the Web Inspector so the
    # auth request can be observed if problems persist.
    'proton.me': {
        'user_agent':            'safari',
        'hardware_acceleration': 'on-demand',
        'developer_tools':       True,
    },
    'protonmail.com': {
        'user_agent':            'safari',
        'hardware_acceleration': 'on-demand',
        'developer_tools':       True,
    },
}

_HW_POLICY = {
    'always':    WebKit2.HardwareAccelerationPolicy.ALWAYS,
    'on-demand': WebKit2.HardwareAccelerationPolicy.ON_DEMAND,
    'never':     WebKit2.HardwareAccelerationPolicy.NEVER,
}

_DEFAULT_COMPAT = {
    'user_agent':            'chrome',    # previous app-wide behaviour, kept
    'hardware_acceleration': 'always',    # as the default for non-listed sites
    'developer_tools':       False,
}


def _resolve_compat(tab: dict, url: str) -> dict:
    compat = dict(_DEFAULT_COMPAT)

    host = urlparse(url).netloc.split(':')[0].lower()
    for domain, overrides in DOMAIN_COMPAT.items():
        if host == domain or host.endswith('.' + domain):
            compat.update(overrides)
            break

    for key in ('user_agent', 'hardware_acceleration', 'developer_tools'):
        if key in tab:
            compat[key] = tab[key]

    return compat


# ── Tab construction ──────────────────────────────────────────────────────────

def build(tab: dict) -> Gtk.Widget:
    url    = tab.get('url', 'about:blank')
    compat = _resolve_compat(tab, url)

    settings = WebKit2.Settings()
    settings.set_enable_javascript(True)
    settings.set_enable_media(True)
    settings.set_enable_webgl(True)
    settings.set_enable_media_stream(True)
    settings.set_javascript_can_access_clipboard(True)
    settings.set_hardware_acceleration_policy(
        _HW_POLICY.get(compat['hardware_acceleration'],
                       WebKit2.HardwareAccelerationPolicy.ALWAYS)
    )
    if compat['developer_tools']:
        # Web Inspector becomes available via right-click → Inspect Element.
        settings.set_enable_developer_extras(True)

    ua = UA_ALIASES.get(compat['user_agent'], compat['user_agent'])
    if ua:
        settings.set_user_agent(ua)

    # Per-tab isolated session — one WebsiteDataManager, WebContext and
    # cookie database per tab. This is intentional (simultaneous logins to
    # multiple accounts on the same service) and must be preserved.
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
    wv.set_hexpand(True)
    wv.set_vexpand(True)

    wv.connect('create', _on_create)
    wv.connect('load-failed-with-tls-errors', _on_tls_error)

    wv.load_uri(url)
    return wv


# ── Popup / new-window handling ───────────────────────────────────────────────

def _on_create(parent_wv, action):
    """
    A page requested a new window (window.open or target=_blank).

    Per the WebKit2 API contract we must return a *new* WebView created with
    new_with_related_view() — it shares the parent's web process, WebContext
    and session (so per-tab isolation is preserved), and keeps the
    window.opener link intact. WebKit performs the navigation itself; we must
    not call load_uri() on the returned view.
    """
    popup_wv = WebKit2.WebView.new_with_related_view(parent_wv)
    popup_wv.set_settings(parent_wv.get_settings())
    popup_wv.set_hexpand(True)
    popup_wv.set_vexpand(True)
    popup_wv.connect('load-failed-with-tls-errors', _on_tls_error)
    # Popups can themselves open popups (rare, but some IdPs do).
    popup_wv.connect('create', _on_create)

    win = _make_popup_window()
    win.add(popup_wv)

    # Show only when WebKit says the window is ready (honours the size /
    # visibility the page requested); destroy when the page calls
    # window.close() — this is how OAuth popups close themselves after
    # posting the result back to the opener.
    popup_wv.connect('ready-to-show', lambda wv: win.show_all())
    popup_wv.connect('close', lambda wv: win.destroy())

    return popup_wv


def _make_popup_window() -> Gtk.Window:
    screen  = Gdk.Screen.get_default()
    monitor = screen.get_primary_monitor()
    geo     = screen.get_monitor_workarea(monitor)
    width   = min(600, int(geo.width * 0.5))
    height  = min(700, int(geo.height * 0.8))

    win = Gtk.Window()
    win.set_default_size(width, height)
    win.set_position(Gtk.WindowPosition.CENTER)
    win.set_keep_above(True)

    header = Gtk.HeaderBar()
    header.set_show_close_button(True)   # manual escape hatch if the site
    header.set_title('Login')            # never calls window.close()
    win.set_titlebar(header)

    return win


# ── TLS (self-signed certs for local services — intentional) ─────────────────

def _on_tls_error(wv, failing_uri, certificate, errors):
    try:
        host = failing_uri.split('/')[2].split(':')[0]
        ctx  = wv.get_context()
        ctx.allow_tls_certificate_for_host(certificate, host)
        wv.load_uri(failing_uri)
    except Exception as e:
        print(f"TLS error handler failed: {e}")
    return True


# ── Panel hooks ───────────────────────────────────────────────────────────────

def reload(widget: Gtk.Widget):
    if isinstance(widget, WebKit2.WebView):
        widget.reload()


# ── Storage paths ─────────────────────────────────────────────────────────────

def _data_dir(tab_id: str) -> str:
    d = Path.home() / '.local' / 'share' / 'quick-panel' / 'tabs' / tab_id
    d.mkdir(parents=True, exist_ok=True)
    return str(d)


def _cache_dir(tab_id: str) -> str:
    d = Path.home() / '.cache' / 'quick-panel' / 'tabs' / tab_id
    d.mkdir(parents=True, exist_ok=True)
    return str(d)


def _cookie_file(tab_id: str) -> str:
    d = Path.home() / '.local' / 'share' / 'quick-panel' / 'tabs' / tab_id
    d.mkdir(parents=True, exist_ok=True)
    return str(d / 'cookies.db')
