"""
SME - Application Settings
Loads configuration from config.ini file
"""
import configparser
from pathlib import Path
from typing import Dict, Any


class AppSettings:
    """Application settings manager"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppSettings, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.config_file = Path("config.ini")
            self.config = configparser.ConfigParser()
            self._load_defaults()
            self._load_from_file()
            self._initialized = True
    
    def _load_defaults(self):
        """Load default settings"""
        self.config['Performance'] = {
            'max_listbox_items': '200',
            'terminal_max_lines': '500',
            'progress_update_interval': '2',
            'memory_cleanup_interval': '10',
            'code_cache_batch_size': '5'
        }
        
        self.config['Export'] = {
            'default_batch_size': '10',
            'auto_save_interval': '300',
            'max_retries': '3',
            'retry_delay': '2'
        }
        
        self.config['UI'] = {
            'theme': 'Dark',
            'window_width': '1280',
            'window_height': '720',
            'enable_fullscreen': 'true'
        }
        
        self.config['Logging'] = {
            'log_level': 'INFO',
            'log_to_file': 'true',
            'log_retention_days': '7',
            'verbose_logging': 'false'
        }
        
        self.config['API'] = {
            'request_timeout': '60',
            'max_code_components': '500',
            'enable_rate_limiting': 'true'
        }
    
    def _load_from_file(self):
        """Load settings from config.ini if it exists"""
        if self.config_file.exists():
            try:
                self.config.read(self.config_file)
                from config.logger import log_info
                log_info("Loaded settings from config.ini", "Settings")
            except Exception as e:
                from config.logger import log_error
                log_error(f"Failed to load config.ini: {str(e)}", "Settings")
        else:
            # Create default config file
            self.save()
    
    def save(self):
        """Save current settings to config.ini"""
        try:
            with open(self.config_file, 'w') as f:
                self.config.write(f)
            from config.logger import log_info
            log_info("Settings saved to config.ini", "Settings")
        except Exception as e:
            from config.logger import log_error
            log_error(f"Failed to save config.ini: {str(e)}", "Settings")
    
    def get(self, section: str, key: str, default: Any = None) -> str:
        """Get setting value"""
        try:
            return self.config.get(section, key)
        except:
            return default
    
    def get_int(self, section: str, key: str, default: int = 0) -> int:
        """Get integer setting value"""
        try:
            return self.config.getint(section, key)
        except:
            return default
    
    def get_bool(self, section: str, key: str, default: bool = False) -> bool:
        """Get boolean setting value"""
        try:
            return self.config.getboolean(section, key)
        except:
            return default
    
    def set(self, section: str, key: str, value: Any):
        """Set setting value"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = str(value)


# Global settings instance
def get_settings():
    """Get application settings instance"""
    return AppSettings()