# Quick Panel

A GTK3 sidebar for Pop!_OS and Ubuntu that gives you instant access to your web apps, local services, files, and documents — without leaving what you're doing.

## Features

- **Web tabs** — embed any web app or local service with persistent sessions and cookie storage
- **File browser tab** — navigate your filesystem with drag and drop, copy, paste, rename, delete
- **Document viewer tab** — open PDFs and local files directly in the panel
- **Divider tabs** — organise your tab strip with labelled section dividers
- **Plugin system** — extend with custom tab types
- **5 themes** — Midnight, Slate, Forest, Ember, Nord — each with dark and light variants
- **Flexible layout** — panel on left or right, tab strip on left or right, three width modes
- **Presets** — one-click prefill for Home Assistant, Music Assistant, Open WebUI
- **Autostart** — optional login startup via desktop entry
- **System tray** — quick access from the tray icon

## Requirements

- Ubuntu 22.04+ or Pop!_OS 22.04+
- Python 3.10+
- GTK3
- WebKit2GTK 4.1

## Install

```bash
git clone gitserver@192.168.1.130:/mnt/git-server/quick-panel .
chmod +x install.sh
bash install.sh
```

## Run

```bash
python3 src/main.py
```

## Tab Types

| Type | Description |
|------|-------------|
| Web / URL | Embeds any website or local service with persistent login |
| File Browser | Full file manager for a chosen directory |
| Document | Opens a specific PDF or local file |
| Divider | Non-clickable label for organising the strip |
| Plugin | Custom tab types from `src/tabs/custom/` |

## Configuration

All settings are saved to `~/.config/quick-panel/config.json` and managed via the Settings panel inside the app. No manual editing required.

Session data, cookies and cache are stored per-tab under:
- `~/.local/share/quick-panel/tabs/<tab-id>/`
- `~/.cache/quick-panel/tabs/<tab-id>/`

## Adding Presets

Presets live in `src/tabs/presets/`. Each file exports a `PRESET` dict:

```python
PRESET = {
    "preset_id": "my-service",
    "label":     "My Service",
    "url":       "http://192.168.1.x:port",
    "type":      "web",
    "icon":      "network-server-symbolic",
}
```

## Adding Plugins

Plugins live in `src/tabs/custom/`. Each file exports `PLUGIN_LABEL` and a `build(tab)` function that returns a `Gtk.Widget`.

## License

MIT
