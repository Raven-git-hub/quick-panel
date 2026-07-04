"""
Manages the Quick Panel autostart and application launcher desktop entries.
"""

from pathlib import Path

APP_NAME    = 'Quick Panel'
DESKTOP_ID  = 'quick-panel'


def _get_src_dir() -> Path:
    return Path(__file__).parent


def _desktop_content() -> str:
    src_dir = _get_src_dir()
    exec_path = src_dir / 'main.py'
    return f"""[Desktop Entry]
Name={APP_NAME}
Comment=Quick access sidebar for your web apps and local services
Exec=python3 {exec_path}
Icon=view-sidebar-symbolic
Terminal=false
Type=Application
Categories=Utility;
StartupNotify=false
"""


def install_launcher():
    """Install the app launcher so it appears in the app drawer."""
    dest = Path.home() / '.local' / 'share' / 'applications' / f'{DESKTOP_ID}.desktop'
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(_desktop_content())


def enable_autostart():
    """Write the autostart entry so the app launches on login."""
    dest = Path.home() / '.config' / 'autostart' / f'{DESKTOP_ID}.desktop'
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(_desktop_content())
    install_launcher()


def disable_autostart():
    """Remove the autostart entry."""
    dest = Path.home() / '.config' / 'autostart' / f'{DESKTOP_ID}.desktop'
    if dest.exists():
        dest.unlink()


def is_autostart_enabled() -> bool:
    """Check if autostart is currently enabled."""
    dest = Path.home() / '.config' / 'autostart' / f'{DESKTOP_ID}.desktop'
    return dest.exists()
