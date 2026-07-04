# Quick Panel

A GTK sidebar for Pop!_OS and Ubuntu that gives you instant access to your 
web apps, local services, and files — without leaving what you're doing.

## Features

- Persistent tabs — web apps, local services, file browser
- Built-in presets for Home Assistant, Music Assistant, and Open WebUI
- Simple URL embedder for anything else (Claude, Portainer, etc.)
- Configurable panel width (quarter, half, full screen)
- System tray icon + Ctrl+` keyboard shortcut

## Requirements

- Ubuntu 22.04+ or Pop!_OS 22.04+
- Python 3.10+

## Install

```bash
bash install.sh
```

## Usage

```bash
python3 src/main.py
```

## Configuration

Tabs and settings are saved to `~/.config/quick-panel/config.json`.  
Edit them via the settings panel (gear icon) inside the app.

## License

MIT
