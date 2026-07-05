"""
Style system for Quick Panel.
All themes and CSS generation live here.
Both panel.py and settings_panel.py import from this module.
"""

# ── Theme definitions ─────────────────────────────────────────────────────────

THEMES = {
    "midnight-dark": {
        "label_family": "Midnight",
        "label_variant": "Midnight",
        "family":   "midnight",
        "variant":  "dark",
        "bg_strip":     "#080a0f",
        "bg_main":      "#0f1117",
        "bg_card":      "#1a1d2e",
        "bg_hover":     "#1a1d2e",
        "border":       "#1e2130",
        "border_card":  "#2d3748",
        "accent":       "#6366f1",
        "accent_hover": "#818cf8",
        "accent_muted": "rgba(99,102,241,0.13)",
        "text":         "#e2e8f0",
        "text_muted":   "#4a5568",
        "text_mid":     "#a0aec0",
        "header_btn":   "#2d3748",
    },
    "midnight-light": {
        "label_family": "Midnight",
        "label_variant": "Midday",
        "family":   "midnight",
        "variant":  "light",
        "bg_strip":     "#f0f0f8",
        "bg_main":      "#f8f8ff",
        "bg_card":      "#e8e8f5",
        "bg_hover":     "#e8e8f5",
        "border":       "#ddd8f0",
        "border_card":  "#ccc8e8",
        "accent":       "#6366f1",
        "accent_hover": "#4f52d4",
        "accent_muted": "rgba(99,102,241,0.13)",
        "text":         "#2d2d5a",
        "text_muted":   "#9090b0",
        "text_mid":     "#5050a0",
        "header_btn":   "#ddd8f0",
    },
    "slate-dark": {
        "label_family": "Slate",
        "label_variant": "Dark Slate",
        "family":   "slate",
        "variant":  "dark",
        "bg_strip":     "#0d0f12",
        "bg_main":      "#111318",
        "bg_card":      "#181c22",
        "bg_hover":     "#181c22",
        "border":       "#1c2028",
        "border_card":  "#2d3748",
        "accent":       "#64748b",
        "accent_hover": "#94a3b8",
        "accent_muted": "rgba(100,116,139,0.15)",
        "text":         "#cbd5e0",
        "text_muted":   "#4a5568",
        "text_mid":     "#a0aec0",
        "header_btn":   "#2d3748",
    },
    "slate-light": {
        "label_family": "Slate",
        "label_variant": "Clean Slate",
        "family":   "slate",
        "variant":  "light",
        "bg_strip":     "#f1f3f5",
        "bg_main":      "#f8f9fa",
        "bg_card":      "#e8eaed",
        "bg_hover":     "#e8eaed",
        "border":       "#dde1e7",
        "border_card":  "#cdd1d9",
        "accent":       "#475569",
        "accent_hover": "#334155",
        "accent_muted": "rgba(71,85,105,0.13)",
        "text":         "#1e293b",
        "text_muted":   "#94a3b8",
        "text_mid":     "#64748b",
        "header_btn":   "#dde1e7",
    },
    "forest-dark": {
        "label_family": "Forest",
        "label_variant": "Dark Forest",
        "family":   "forest",
        "variant":  "dark",
        "bg_strip":     "#0a0f0a",
        "bg_main":      "#0c120c",
        "bg_card":      "#162016",
        "bg_hover":     "#162016",
        "border":       "#1a2a1a",
        "border_card":  "#1a3a1a",
        "accent":       "#4ade80",
        "accent_hover": "#86efac",
        "accent_muted": "rgba(74,222,128,0.13)",
        "text":         "#d1fae5",
        "text_muted":   "#4a6a4a",
        "text_mid":     "#8aaa8a",
        "header_btn":   "#1a3a1a",
    },
    "forest-light": {
        "label_family": "Forest",
        "label_variant": "Light Forest",
        "family":   "forest",
        "variant":  "light",
        "bg_strip":     "#f0f7f0",
        "bg_main":      "#f7fdf7",
        "bg_card":      "#e4f0e4",
        "bg_hover":     "#e4f0e4",
        "border":       "#d4e8d4",
        "border_card":  "#b8d8b8",
        "accent":       "#16a34a",
        "accent_hover": "#15803d",
        "accent_muted": "rgba(22,163,74,0.13)",
        "text":         "#14532d",
        "text_muted":   "#86a886",
        "text_mid":     "#3a7a3a",
        "header_btn":   "#d4e8d4",
    },
    "ember-dark": {
        "label_family": "Ember",
        "label_variant": "Ember",
        "family":   "ember",
        "variant":  "dark",
        "bg_strip":     "#0f0a08",
        "bg_main":      "#120c08",
        "bg_card":      "#201408",
        "bg_hover":     "#201408",
        "border":       "#2a1a10",
        "border_card":  "#3a2010",
        "accent":       "#f97316",
        "accent_hover": "#fb923c",
        "accent_muted": "rgba(249,115,22,0.13)",
        "text":         "#fed7aa",
        "text_muted":   "#6a4a3a",
        "text_mid":     "#aa8a7a",
        "header_btn":   "#3a2010",
    },
    "ember-light": {
        "label_family": "Ember",
        "label_variant": "Daybreak",
        "family":   "ember",
        "variant":  "light",
        "bg_strip":     "#fdf5f0",
        "bg_main":      "#fffaf7",
        "bg_card":      "#f8ede4",
        "bg_hover":     "#f8ede4",
        "border":       "#f0d8c8",
        "border_card":  "#e8c8a8",
        "accent":       "#ea580c",
        "accent_hover": "#c2410c",
        "accent_muted": "rgba(234,88,12,0.13)",
        "text":         "#7c2d12",
        "text_muted":   "#c0906a",
        "text_mid":     "#a05030",
        "header_btn":   "#f0d8c8",
    },
    "nord-dark": {
        "label_family": "Nord",
        "label_variant": "Nord",
        "family":   "nord",
        "variant":  "dark",
        "bg_strip":     "#242933",
        "bg_main":      "#2e3440",
        "bg_card":      "#3b4252",
        "bg_hover":     "#3b4252",
        "border":       "#2e3440",
        "border_card":  "#434c5e",
        "accent":       "#88c0d0",
        "accent_hover": "#8fbcbb",
        "accent_muted": "rgba(136,192,208,0.13)",
        "text":         "#eceff4",
        "text_muted":   "#4c566a",
        "text_mid":     "#d8dee9",
        "header_btn":   "#3b4252",
    },
    "nord-light": {
        "label_family": "Nord",
        "label_variant": "Nordic",
        "family":   "nord",
        "variant":  "light",
        "bg_strip":     "#e5e9f0",
        "bg_main":      "#eceff4",
        "bg_card":      "#d8dee9",
        "bg_hover":     "#d8dee9",
        "border":       "#d8dee9",
        "border_card":  "#c8d0df",
        "accent":       "#5e81ac",
        "accent_hover": "#4c6f9a",
        "accent_muted": "rgba(94,129,172,0.13)",
        "text":         "#2e3440",
        "text_muted":   "#aebacf",
        "text_mid":     "#4c566a",
        "header_btn":   "#d8dee9",
    },
}

# Font sizes
FONT_SIZES = {
    "small":  10,
    "medium": 12,
    "large":  14,
}

# Default theme
DEFAULT_THEME    = "midnight-dark"
DEFAULT_FONT     = "small"


def get_theme(theme_id: str) -> dict:
    """Return theme dict, falling back to default if not found."""
    return THEMES.get(theme_id, THEMES[DEFAULT_THEME])


def get_families() -> list:
    """Return list of unique theme families with their dark/light ids."""
    seen = {}
    for theme_id, theme in THEMES.items():
        family = theme['family']
        if family not in seen:
            seen[family] = {'dark': None, 'light': None, 'label': theme['label_family']}
        seen[family][theme['variant']] = theme_id
    return list(seen.values())


def generate_panel_css(theme_id: str, font_size: str) -> str:
    """Generate CSS for the main panel window."""
    t  = get_theme(theme_id)
    fs = FONT_SIZES.get(font_size, FONT_SIZES[DEFAULT_FONT])

    return f"""
window {{
    background-color: {t['bg_main']};
}}
.icon-strip {{
    background-color: {t['bg_strip']};
    border-right: 1px solid {t['border']};
}}
.tab-btn {{
    background: transparent;
    border: none;
    border-radius: 0;
    padding: 8px 10px;
    color: {t['text_muted']};
}}
.tab-btn:hover {{
    background-color: {t['bg_hover']};
    color: {t['text_mid']};
}}
.tab-btn.active {{
    background-color: {t['bg_hover']};
    color: {t['accent']};
    border-left: 2px solid {t['accent']};
}}
.tab-label {{
    color: {t['text_muted']};
    font-size: {fs}px;
}}
.tab-btn:hover .tab-label {{
    color: {t['text_mid']};
}}
.tab-btn.active .tab-label {{
    color: {t['accent']};
}}
.header {{
    background-color: {t['bg_strip']};
    border-bottom: 1px solid {t['border']};
    min-height: 38px;
}}
.header-title {{
    color: {t['text']};
    font-size: 13px;
    font-weight: 500;
}}
.header-btn {{
    background: transparent;
    border: none;
    border-radius: 4px;
    color: {t['text_muted']};
    padding: 4px;
    min-width: 28px;
    min-height: 28px;
}}
.header-btn:hover {{
    background-color: {t['header_btn']};
    color: {t['text']};
}}
.settings-btn {{
    background: transparent;
    border: none;
    border-radius: 0;
    padding: 8px 10px;
    color: {t['text_muted']};
}}
.settings-btn:hover {{
    background-color: {t['bg_hover']};
    color: {t['text_mid']};
}}
"""


def generate_settings_css(theme_id: str, font_size: str) -> str:
    """Generate CSS for the settings panel."""
    t  = get_theme(theme_id)
    fs = FONT_SIZES.get(font_size, FONT_SIZES[DEFAULT_FONT])

    return f"""
.settings-root {{
    background-color: {t['bg_main']};
}}
.settings-section-label {{
    color: {t['text_muted']};
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.08em;
}}
.settings-card {{
    background-color: {t['bg_card']};
    border-radius: 8px;
    border: 1px solid {t['border_card']};
}}
.width-btn {{
    background: transparent;
    border: 1px solid {t['border_card']};
    border-radius: 6px;
    color: {t['text_mid']};
    padding: 6px 12px;
    font-size: 12px;
}}
.width-btn:hover {{
    background-color: {t['bg_card']};
    color: {t['text']};
}}
.width-btn.active {{
    background-color: {t['accent']};
    border-color: {t['accent']};
    color: #ffffff;
}}
.tab-row {{
    background-color: {t['bg_card']};
    border-radius: 6px;
    border: 1px solid {t['border_card']};
    padding: 4px;
}}
.tab-row-btn {{
    background: transparent;
    border: none;
    border-radius: 4px;
    color: {t['text_muted']};
    padding: 4px;
    min-width: 26px;
    min-height: 26px;
}}
.tab-row-btn:hover {{
    background-color: {t['header_btn']};
    color: {t['text']};
}}
.tab-row-btn.delete:hover {{
    background-color: #742a2a;
    color: #fc8181;
}}
.add-btn {{
    background-color: {t['accent']};
    border: none;
    border-radius: 6px;
    color: #ffffff;
    padding: 8px 16px;
    font-size: 12px;
    font-weight: 500;
}}
.add-btn:hover {{
    background-color: {t['accent_hover']};
}}
.form-entry {{
    background-color: {t['bg_card']};
    border: 1px solid {t['border_card']};
    border-radius: 6px;
    color: {t['text']};
    padding: 6px 10px;
    font-size: 12px;
}}
.form-entry:focus {{
    border-color: {t['accent']};
}}
.form-label {{
    color: {t['text_mid']};
    font-size: {fs}px;
}}
.icon-btn {{
    background: transparent;
    border: 1px solid {t['border_card']};
    border-radius: 6px;
    color: {t['text_muted']};
    padding: 6px;
    min-width: 36px;
    min-height: 36px;
}}
.icon-btn:hover {{
    background-color: {t['bg_card']};
    color: {t['text_mid']};
}}
.icon-btn.selected {{
    border-color: {t['accent']};
    background-color: {t['accent_muted']};
    color: {t['accent']};
}}
.back-btn {{
    background: transparent;
    border: none;
    border-radius: 4px;
    color: {t['text_muted']};
    padding: 4px 8px;
    font-size: 12px;
}}
.back-btn:hover {{
    background-color: {t['bg_card']};
    color: {t['text_mid']};
}}
.header-title {{
    color: {t['text']};
    font-size: 13px;
    font-weight: 500;
}}
.divider {{
    background-color: {t['border']};
}}
.preset-divider {{
    background-color: {t['border_card']};
}}
.theme-btn {{
    background: transparent;
    border: 1px solid {t['border_card']};
    border-radius: 6px;
    color: {t['text_mid']};
    padding: 6px 12px;
    font-size: 12px;
}}
.theme-btn:hover {{
    background-color: {t['bg_card']};
    color: {t['text']};
}}
.theme-btn.active {{
    background-color: {t['accent']};
    border-color: {t['accent']};
    color: #ffffff;
}}
switch {{
    background-color: {t['border_card']};
    border-radius: 14px;
    border: none;
}}
switch:checked {{
    background-color: {t['accent']};
}}
switch slider {{
    background-color: {t['text']};
    border-radius: 12px;
    min-width: 24px;
    min-height: 24px;
}}
"""
