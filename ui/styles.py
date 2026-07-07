"""
UI Styles & Theme Configuration (styles.py)

Defines color palettes, fonts, and widget styles for the Tkinter GUI.

Author: [Your Name]
Date: 2026
"""

# ── Color Palette (Dark Theme) ─────────────────────────────────────────
DARK_THEME = {
    "bg_primary":     "#0D1117",   # Main window background
    "bg_secondary":   "#161B22",   # Panels / frames
    "bg_card":        "#1C2128",   # Card / section backgrounds
    "bg_input":       "#21262D",   # Input fields
    "accent":         "#2EA043",   # Primary action (green)
    "accent_hover":   "#3FB950",   # Hover state
    "accent_danger":  "#DA3633",   # Danger / stop
    "accent_warn":    "#E3B341",   # Warning / secondary action
    "accent_blue":    "#388BFD",   # Info / links
    "text_primary":   "#E6EDF3",   # Main text
    "text_secondary": "#8B949E",   # Secondary / muted text
    "border":         "#30363D",   # Borders & dividers
}

# ── Color Palette (Light Theme) ─────────────────────────────────────────
LIGHT_THEME = {
    "bg_primary":     "#FFFFFF",
    "bg_secondary":   "#F6F8FA",
    "bg_card":        "#FFFFFF",
    "bg_input":       "#F6F8FA",
    "accent":         "#1A7F37",
    "accent_hover":   "#2EA043",
    "accent_danger":  "#CF222E",
    "accent_warn":    "#9A6700",
    "accent_blue":    "#0969DA",
    "text_primary":   "#1F2328",
    "text_secondary": "#656D76",
    "border":         "#D0D7DE",
}

# ── Fonts ─────────────────────────────────────────────────────────────
FONTS = {
    "title":      ("Segoe UI", 16, "bold"),
    "heading":    ("Segoe UI", 12, "bold"),
    "body":       ("Segoe UI", 10),
    "body_bold":  ("Segoe UI", 10, "bold"),
    "small":      ("Segoe UI", 9),
    "mono":       ("Consolas", 10),
    "mono_large": ("Consolas", 11),
}

# ── Padding & Sizing ─────────────────────────────────────────────────
PAD = {
    "xs":  4,
    "sm":  8,
    "md":  12,
    "lg":  16,
    "xl":  24,
}

# ── Button Styles ─────────────────────────────────────────────────────
BUTTON_STYLE = {
    "relief":        "flat",
    "borderwidth":   0,
    "cursor":        "hand2",
    "padx":          14,
    "pady":          7,
}
