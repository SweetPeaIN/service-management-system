"""
app/profile_ui.py
-----------------
Handles the visual presentation of the User Profile.
Contains both the static assets (ASCII art, Themes) and the rendering logic.
"""

import random
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from rich.console import Group
from rich.rule import Rule
from app.models import User

console = Console()

# --- ASSETS (DATA) ---

AVATARS = [
    r"""
    ▄▄▄▄▄▄▄
   █  o  o █
   █   ▀   █
   █ \___/ █
    ▀▀▀▀▀▀▀
    """,
    r"""
      /---\
     | @ @ |
     |  ^  |
     | (_) |
      \___/
    """,
    r"""
    .-------.
    | [-_-] |
    |  ___  |
    | |___| |
    '-------'
    """,
    r"""
      _   _
     (o) (o)
    (   v   )
     \ --- /
      '---'
    """,
    r"""
     / \__
    (    @\___
    /         O
   /   (_____/
  /_____/
    """
]

THEMES = [
    {"name": "Cyberpunk", "border": "bold magenta", "title": "bold cyan", "text": "bright_white"},
    {"name": "Hacker",    "border": "bold green",   "title": "bold green", "text": "green"},
    {"name": "Retro",     "border": "bold yellow",  "title": "bold red",   "text": "yellow"},
    {"name": "Oceanic",   "border": "bold blue",    "title": "bold blue",  "text": "cyan"},
    {"name": "Monochrome","border": "white",        "title": "bold white", "text": "dim white"},
]

LAYOUT_STYLES = [box.ROUNDED, box.DOUBLE, box.HEAVY, box.ASCII, box.HORIZONTALS]

HEADERS = [
    "─ IDENTITY CARD ─", "• USER PROFILE •", "| ACCESS GRANTED |", "~ SYSTEM DATA ~"
]

# --- RENDERER (LOGIC) ---

def render_profile_dashboard(user: User):
    """
    Clears the screen and draws a randomized Profile Card for the given user.
    """
    console.clear()

    # 1. Randomizer Engine
    avatar = random.choice(AVATARS)
    theme = random.choice(THEMES)
    box_style = random.choice(LAYOUT_STYLES)
    header_text = random.choice(HEADERS)

    # 2. Component Construction
    
    # A. Avatar (Centered & Colored)
    avatar_renderable = Align.center(Text(avatar, style=theme["title"]))

    # B. User Details (Styled Text)
    details_text = Text()
    details_text.append("\nUser ID: ", style=f"bold {theme['border']}")
    details_text.append(f"{user.id}\n", style=theme["text"])
    
    details_text.append("Name:    ", style=f"bold {theme['border']}")
    details_text.append(f"{user.user_name}\n", style=theme["text"])
    
    details_text.append("Email:   ", style=f"bold {theme['border']}")
    details_text.append(f"{user.email}\n", style=theme["text"])
    
    details_text.append("Address: ", style=f"bold {theme['border']}")
    details_text.append(f"{user.address}", style=theme["text"])

    # C. Grouping
    card_content = Group(
        avatar_renderable,
        Rule(style=theme["border"]),
        Align.left(details_text)
    )

    # D. The Panel
    profile_card = Panel(
        card_content,
        title=header_text,
        subtitle=f"Theme: {theme['name']}",
        style=theme["border"],
        box=box_style,
        width=50,
        padding=(1, 2)
    )

    # 3. Final Output
    console.print(Align.center(profile_card))
    console.print("\n")