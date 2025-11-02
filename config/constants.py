"""
SME (Salesforce Metadata Exporter) - Configuration Constants
"""
import os

# Application Info
APP_NAME = "SME"
APP_FULL_NAME = "Salesforce Metadata Exporter"
APP_VERSION = "2.0.0"

# Window Configuration
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = f"{APP_NAME} - {APP_FULL_NAME}"

# API Configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
REQUEST_TIMEOUT = 60  # seconds

# File Limits
EXCEL_MAX_ROWS = 1048576
CSV_MAX_ROWS = 1000000

# UI Colors - Dark Theme
COLOR_PRIMARY = "#1F6AA5"
COLOR_SUCCESS = "#28a745"
COLOR_WARNING = "#FFA500"
COLOR_DANGER = "#CC3333"
COLOR_INFO = "#17a2b8"

# UI Colors - Buttons
BUTTON_EXPORT = "#28a745"
BUTTON_EXPORT_HOVER = "#218838"
BUTTON_CANCEL = "#FF6B6B"
BUTTON_PLACEHOLDER = "#6c757d"

# Terminal/Console Settings
TERMINAL_FONT = ("Consolas", 12)
TERMINAL_HEIGHT = 200  # pixels
TERMINAL_BG_DARK = "#1e1e1e"
TERMINAL_FG_DARK = "#d4d4d4"
TERMINAL_BG_LIGHT = "#ffffff"
TERMINAL_FG_LIGHT = "#000000"

# Directories
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)