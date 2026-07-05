"""
Config system for Quick Panel.
Loads and saves ~/.config/quick-panel/config.json.
On first run, writes a default config with no tabs.
"""

import json
from pathlib import Path

CONFIG_DIR  = Path.home() / ".config" / "quick-panel"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "width":     "medium",
    "theme":     "midnight-dark",
    "font_size": "small",
    "position":  "right",
    "tabs":      []
}


def load() -> dict:
    if not CONFIG_FILE.exists():
        save(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        backup = CONFIG_FILE.with_suffix(".json.bak")
        CONFIG_FILE.rename(backup)
        save(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()


def save(config: dict) -> None:
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
    assert width in ("narrow", "medium", "wide")
    config["width"] = width
    save(config)
    return config


def set_theme(config: dict, theme_id: str) -> dict:
    config["theme"] = theme_id
    save(config)
    return config


def set_font_size(config: dict, font_size: str) -> dict:
    assert font_size in ("small", "medium", "large")
    config["font_size"] = font_size
    save(config)
    return config
