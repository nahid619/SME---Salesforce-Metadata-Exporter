"""
SME - Logging Configuration
Provides structured logging to file and console
"""
import logging
import os
from datetime import datetime
from pathlib import Path


class SMELogger:
    """Centralized logging for SME application"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SMELogger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._setup_logger()
            SMELogger._initialized = True
    
    def _setup_logger(self):
        """Setup application logger with file and console handlers"""
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Generate log filename with date
        log_filename = log_dir / f"sme_{datetime.now().strftime('%Y%m%d')}.log"
        
        # Configure root logger
        self.logger = logging.getLogger('SME')
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        # File handler - detailed logs
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # Console handler - important logs only
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.logger.info("=" * 70)
        self.logger.info("SME Application Started")
        self.logger.info("=" * 70)
    
    def get_logger(self, name: str = None):
        """Get logger instance for a specific module"""
        if name:
            return logging.getLogger(f'SME.{name}')
        return self.logger
    
    def log_exception(self, exception: Exception, context: str = ""):
        """Log exception with full traceback"""
        import traceback
        self.logger.error(f"Exception in {context}: {str(exception)}")
        self.logger.error(f"Traceback:\n{traceback.format_exc()}")
    
    def log_export_stats(self, export_type: str, stats: dict, runtime: str):
        """Log export statistics in structured format"""
        self.logger.info("-" * 70)
        self.logger.info(f"{export_type} Export Statistics:")
        self.logger.info(f"  Runtime: {runtime}")
        self.logger.info(f"  API Calls: {stats.get('api_calls_made', 0)}")
        self.logger.info(f"  Objects Processed: {stats.get('successful_objects', 0)}/{stats.get('total_objects', 0)}")
        self.logger.info(f"  Status: {'CANCELLED' if stats.get('cancelled') else 'COMPLETED'}")
        self.logger.info("-" * 70)
    
    def log_performance(self, operation: str, duration: float, details: dict = None):
        """Log performance metrics"""
        self.logger.info(f"Performance: {operation} took {duration:.2f}s")
        if details:
            for key, value in details.items():
                self.logger.info(f"  {key}: {value}")
    
    def cleanup_old_logs(self, days_to_keep: int = 7):
        """Remove log files older than specified days"""
        log_dir = Path("logs")
        if not log_dir.exists():
            return
        
        cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
        
        for log_file in log_dir.glob("sme_*.log"):
            if log_file.stat().st_mtime < cutoff_date:
                try:
                    log_file.unlink()
                    self.logger.info(f"Deleted old log file: {log_file.name}")
                except Exception as e:
                    self.logger.error(f"Failed to delete {log_file.name}: {str(e)}")


# Global logger instance
def get_logger(name: str = None):
    """Get logger instance - use this in all modules"""
    return SMELogger().get_logger(name)


# Convenience functions
def log_info(message: str, module: str = None):
    """Log info message"""
    get_logger(module).info(message)


def log_error(message: str, module: str = None):
    """Log error message"""
    get_logger(module).error(message)


def log_warning(message: str, module: str = None):
    """Log warning message"""
    get_logger(module).warning(message)


def log_debug(message: str, module: str = None):
    """Log debug message"""
    get_logger(module).debug(message)


def log_exception(exception: Exception, context: str = "", module: str = None):
    """Log exception with traceback"""
    SMELogger().log_exception(exception, context)