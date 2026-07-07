#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  Quick Panel — installer
#  Supports Ubuntu 22.04+ and Pop!_OS 22.04+
# ─────────────────────────────────────────────────────────────
set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="Quick Panel"
DESKTOP_ID="quick-panel"

echo ""
echo "  ╔═══════════════════════════════╗"
echo "  ║       Quick Panel Setup       ║"
echo "  ╚═══════════════════════════════╝"
echo ""

# ── Detect distro ─────────────────────────────────────────────
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
else
    DISTRO="unknown"
fi

if [[ "$DISTRO" != "ubuntu" && "$DISTRO" != "pop" ]]; then
    echo "  ⚠  Warning: $PRETTY_NAME is not officially supported."
    echo "     Continuing anyway — it may still work."
    echo ""
fi

# ── System dependencies ───────────────────────────────────────
echo "→ Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y \
    python3 \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gtk-3.0 \
    gir1.2-webkit2-4.1 \
    gir1.2-ayatanaappindicator3-0.1 \
    gir1.2-gio-2.0 \
    cifs-utils

echo "   ✓ Core dependencies installed."

# ── Optional: Wayland layer shell support ─────────────────────
echo ""
echo "→ Installing Wayland layer shell support..."
sudo apt-get install -y gir1.2-gtklayershell-0.1 2>/dev/null && \
    echo "   ✓ GtkLayerShell installed — Wayland positioning supported." || \
    echo "   ⚠  GtkLayerShell not available — panel may not position correctly on Wayland."

# ── Optional: keyboard shortcut support ───────────────────────
echo ""
echo "→ Installing optional keybinder3 (Ctrl+\` shortcut)..."
sudo apt-get install -y gir1.2-keybinder-3.0 2>/dev/null && \
    echo "   ✓ keybinder3 installed." || \
    echo "   ⚠  keybinder3 not available — Ctrl+\` shortcut won't work."

# ── App launcher desktop entry ────────────────────────────────
echo ""
echo "→ Installing app launcher..."
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"

cat > "$DESKTOP_DIR/$DESKTOP_ID.desktop" << EOF
[Desktop Entry]
Name=$APP_NAME
Comment=Quick access sidebar for your web apps and local services
Exec=python3 $REPO_DIR/src/main.py
Icon=view-sidebar-symbolic
Terminal=false
Type=Application
Categories=Utility;
StartupNotify=false
EOF

echo "   ✓ App launcher installed — search '$APP_NAME' in your app drawer."

# ── Autostart ─────────────────────────────────────────────────
echo ""
read -p "→ Start Quick Panel automatically on login? [y/N] " autostart
if [[ "$autostart" =~ ^[Yy]$ ]]; then
    mkdir -p "$HOME/.config/autostart"
    cp "$DESKTOP_DIR/$DESKTOP_ID.desktop" \
       "$HOME/.config/autostart/$DESKTOP_ID.desktop"
    echo "   ✓ Autostart enabled."
else
    echo "   — Autostart skipped. You can enable it later in Settings."
fi

# ── Session type info ─────────────────────────────────────────
SESSION=$(echo "$XDG_SESSION_TYPE")
if [[ "$SESSION" == "wayland" ]]; then
    echo ""
    echo "  ✓ Wayland detected — GtkLayerShell will handle panel positioning."
else
    echo ""
    echo "  ✓ X11 detected — standard window positioning will be used."
fi

# ── Done ──────────────────────────────────────────────────────
echo ""
echo "  ╔═══════════════════════════════╗"
echo "  ║         Setup complete!       ║"
echo "  ╚═══════════════════════════════╝"
echo ""
echo "  Run with:"
echo "    python3 $REPO_DIR/src/main.py"
echo ""
echo "  Or search '$APP_NAME' in your app drawer."
echo ""
