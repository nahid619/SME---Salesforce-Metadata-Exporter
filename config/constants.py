"""
SME (Salesforce Metadata Exporter) - Configuration Constants
"""
import os
from config.settings import get_settings

# Load settings
_settings = get_settings()

# Application Info
APP_NAME = "SME"
APP_FULL_NAME = "Salesforce Metadata Exporter"
APP_VERSION = "2.1.1"  # Bug fix release

# Window Configuration
WINDOW_WIDTH = _settings.get_int('UI', 'window_width', 1280)
WINDOW_HEIGHT = _settings.get_int('UI', 'window_height', 720)
WINDOW_TITLE = f"{APP_NAME} - {APP_FULL_NAME}"

# API Configuration
MAX_RETRIES = _settings.get_int('Export', 'max_retries', 3)
RETRY_DELAY = _settings.get_int('Export', 'retry_delay', 2)
REQUEST_TIMEOUT = _settings.get_int('API', 'request_timeout', 60)

# Performance Settings
MAX_LISTBOX_ITEMS = _settings.get_int('Performance', 'max_listbox_items', 200)
TERMINAL_MAX_LINES = _settings.get_int('Performance', 'terminal_max_lines', 500)
PROGRESS_UPDATE_INTERVAL = _settings.get_int('Performance', 'progress_update_interval', 2)
MEMORY_CLEANUP_INTERVAL = _settings.get_int('Performance', 'memory_cleanup_interval', 10)
CODE_CACHE_BATCH_SIZE = _settings.get_int('Performance', 'code_cache_batch_size', 5)

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

# API Limits
MAX_CODE_COMPONENTS = _settings.get_int('API', 'max_code_components', 500)

# Directories
import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)