"""
Configuration Module for Smart Expense Tracker with Analytics.
Manages application settings, database credentials, theme styling tokens,
and environment persistence.
"""

import os
from pathlib import Path
from dotenv import load_dotenv, set_key

# Root project directory
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

# Load environment variables
if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE, override=True)
else:
    load_dotenv()


class ThemeColors:
    """Color palette matching the purple/lavender modern finance dashboard reference."""
    PRIMARY = "#7C5CFC"          # Vibrant modern purple
    PRIMARY_HOVER = "#6B4CF0"    # Darker purple hover
    PRIMARY_LIGHT = "#EDE9FE"    # Soft lavender accent background
    SECONDARY = "#B4A5F5"        # Light purple pill accent
    ACCENT_PURPLE = "#8B5CF6"    # Rich purple
    
    # Backgrounds
    BG_WINDOW = "#F7F8FC"        # Modern off-white / light slate canvas
    BG_CARD = "#FFFFFF"          # Crisp white card surface
    BG_SIDEBAR = "#FFFFFF"       # White vertical sidebar
    BG_MUTED = "#F1F3F9"         # Subtle pill background
    
    # Borders & Dividers
    BORDER_SUBTLE = "#E5E7EB"    # Card & container borders
    BORDER_FOCUS = "#7C5CFC"     # Input focus border
    
    # Text colors
    TEXT_MAIN = "#1E1B4B"        # Deep indigo/slate for primary text
    TEXT_MUTED = "#64748B"       # Slate gray for secondary labels
    TEXT_LIGHT = "#94A3B8"       # Light gray for hints
    TEXT_ON_PRIMARY = "#FFFFFF"  # White text on purple buttons
    
    # Semantic alert colors
    SUCCESS = "#10B981"          # Green for savings / income
    DANGER = "#EF4444"           # Red for high expenses / exceeded budget
    WARNING = "#F59E0B"          # Amber for budget warnings
    INFO = "#3B82F6"             # Blue for info notifications
    
    # Chart palettes (Harmonious purple, cyan-lavender, pink-violet shades)
    CHART_PALETTE = [
        "#7C5CFC",  # Deep Purple
        "#A78BFA",  # Medium Lavender
        "#C4B5FD",  # Soft Violet
        "#DDD6FE",  # Pale Lilac
        "#818CF8",  # Periwinkle
        "#38BDF8",  # Cyan Accent
        "#F472B6",  # Pink/Magenta Accent
        "#FBBF24",  # Amber
        "#34D399",  # Mint Emerald
        "#93C5FD",  # Sky Blue
        "#E879F9",  # Neon Fuchsia
        "#A855F7"   # Royal Purple
    ]


class FontConfig:
    """Typography settings ensuring cross-platform readability."""
    FAMILY = "Segoe UI"
    FAMILY_FALLBACK = "Arial"
    
    HEADER_LARGE = (FAMILY, 24, "bold")
    HEADER_MEDIUM = (FAMILY, 16, "bold")
    HEADER_SMALL = (FAMILY, 13, "bold")
    BODY = (FAMILY, 10, "normal")
    BODY_BOLD = (FAMILY, 10, "bold")
    BODY_SMALL = (FAMILY, 9, "normal")
    METRIC_LARGE = (FAMILY, 28, "bold")
    METRIC_LABEL = (FAMILY, 9, "normal")
    BUTTON = (FAMILY, 10, "bold")


class AppConfig:
    """Application and Database runtime configuration."""
    APP_NAME = "Smart Expense Tracker with Analytics"
    VERSION = "2.0.0"
    CURRENCY_SYMBOL = "₹"
    
    # Window dimensions
    MIN_WINDOW_WIDTH = 1200
    MIN_WINDOW_HEIGHT = 750
    DEFAULT_WINDOW_WIDTH = 1280
    DEFAULT_WINDOW_HEIGHT = 800

    @classmethod
    def get_oracle_user(cls) -> str:
        return os.getenv("ORACLE_USER", "expense_tracker")

    @classmethod
    def get_oracle_password(cls) -> str:
        return os.getenv("ORACLE_PASSWORD", "ExpenseTracker123#")

    @classmethod
    def get_oracle_host(cls) -> str:
        return os.getenv("ORACLE_HOST", "localhost")

    @classmethod
    def get_oracle_port(cls) -> str:
        return os.getenv("ORACLE_PORT", "1521")

    @classmethod
    def get_oracle_service_name(cls) -> str:
        return os.getenv("ORACLE_SERVICE_NAME", "xe")

    @classmethod
    def get_oracle_dsn(cls) -> str:
        dsn = os.getenv("ORACLE_DSN")
        if dsn and dsn.strip():
            return dsn.strip()
        host = cls.get_oracle_host()
        port = cls.get_oracle_port()
        svc = cls.get_oracle_service_name()
        return f"{host}:{port}/{svc}"

    @classmethod
    def get_oracle_client_dir(cls) -> str:
        client_dir = os.getenv("ORACLE_CLIENT_DIR", "")
        if client_dir:
            # Check relative to base directory
            p = BASE_DIR / client_dir
            if p.exists():
                return str(p.resolve())
            if Path(client_dir).exists():
                return str(Path(client_dir).resolve())
        # Default auto-discovery of local instantclient directory
        for item in BASE_DIR.glob("instantclient*"):
            if item.is_dir() and (item / "oci.dll").exists():
                return str(item.resolve())
        return ""

    @classmethod
    def get_default_user_id(cls) -> int:
        try:
            return int(os.getenv("DEFAULT_USER_ID", "1"))
        except ValueError:
            return 1

    @classmethod
    def get_default_username(cls) -> str:
        return os.getenv("DEFAULT_USERNAME", "demo_user")

    @classmethod
    def save_settings(cls, user: str, password: str, host: str, port: str, service: str, client_dir: str = ""):
        """Persist updated database settings to .env file."""
        if not ENV_FILE.exists():
            ENV_FILE.touch()
        
        dsn = f"{host}:{port}/{service}"
        set_key(str(ENV_FILE), "ORACLE_USER", user)
        set_key(str(ENV_FILE), "ORACLE_PASSWORD", password)
        set_key(str(ENV_FILE), "ORACLE_HOST", host)
        set_key(str(ENV_FILE), "ORACLE_PORT", port)
        set_key(str(ENV_FILE), "ORACLE_SERVICE_NAME", service)
        set_key(str(ENV_FILE), "ORACLE_DSN", dsn)
        if client_dir:
            set_key(str(ENV_FILE), "ORACLE_CLIENT_DIR", client_dir)
        
        # Reload environment
        load_dotenv(dotenv_path=ENV_FILE, override=True)
