"""
Config system for Quick Panel.
Loads and saves ~/.config/quick-panel/config.json.
On first run, writes a default config with the three presets.
"""

import json
import os
from pathlib import Path

CONFIG_DIR  = Path.home() / ".config" / "quick-panel"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "width": "half",       # quarter | half | full
    "position": "right",   # right | left (future)
    "tabs": [
        {
            "id": "home_assistant",
            "type": "preset",
            "label": "Home Assistant",
            "preset_id": "home_assistant",
            "url": "http://homeassistant.local:8123",
            "token": "",
            "icon": "network-server-symbolic"
        },
        {
            "id": "music_assistant",
            "type": "preset",
            "label": "Music Assistant",
            "preset_id": "music_assistant",
            "url": "http://homeassistant.local:8095",
            "token": "",
            "icon": "audio-x-generic-symbolic"
        },
        {
            "id": "open_webui",
            "type": "preset",
            "label": "Open WebUI",
            "preset_id": "open_webui",
            "url": "http://localhost:3000",
            "token": "",
            "icon": "applications-science-symbolic"
        }
    ]
}


def load() -> dict:
    """Load config from disk. Writes defaults if file doesn't exist."""
    if not CONFIG_FILE.exists():
        save(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        # Corrupted config — back it up and return defaults
        backup = CONFIG_FILE.with_suffix(".json.bak")
        CONFIG_FILE.rename(backup)
        save(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()


def save(config: dict) -> None:
    """Persist config to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def add_tab(config: dict, tab: dict) -> dict:
    config["tabs"].append(tab)
    save(config)
    return config


def remove_tab(config: dict, tab_id: str) -> dict:
    config["tabs"] = [t for t in config["tabs"] if t["id"] != tab_id]
    save(config)
    return config


def reorder_tabs(config: dict, new_order: list) -> dict:
    """new_order is a list of tab ids in the desired order."""
    tab_map = {t["id"]: t for t in config["tabs"]}
    config["tabs"] = [tab_map[tid] for tid in new_order if tid in tab_map]
    save(config)
    return config


def update_tab(config: dict, tab_id: str, updates: dict) -> dict:
    for tab in config["tabs"]:
        if tab["id"] == tab_id:
            tab.update(updates)
            break
    save(config)
    return config


def set_width(config: dict, width: str) -> dict:
    assert width in ("quarter", "half", "full")
    config["width"] = width
    save(config)
    return config
