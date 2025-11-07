"""
Base Detector Class
Common functionality for all usage detectors
"""
from typing import Dict, List, Optional, Callable
from abc import ABC, abstractmethod


class BaseDetector(ABC):
    """Base class for all field usage detectors"""
    
    def __init__(self, sf_client, log_callback: Optional[Callable] = None):
        """
        Initialize detector
        
        Args:
            sf_client: Salesforce client instance
            log_callback: Optional callback for logging
        """
        self.sf_client = sf_client
        self.log_callback = log_callback
        self.cache = {}
    
    def _log(self, message: str, verbose: bool = False):
        """Internal logging helper"""
        if self.log_callback:
            self.log_callback(message, verbose=verbose)
    
    @abstractmethod
    def detect_usage(self, object_name: str) -> Dict[str, List[str]]:
        """
        Detect field usage for given object
        Must be implemented by subclasses
        
        Args:
            object_name: API name of the object
            
        Returns:
            Dictionary mapping field names to list of where they're used
            Example: {'Name': ['Account Layout', 'Sales Layout'], 'Amount': ['Opp Layout']}
        """
        pass
    
    def get_cached_usage(self, object_name: str) -> Optional[Dict[str, List[str]]]:
        """Get cached usage data if available"""
        return self.cache.get(object_name)
    
    def set_cached_usage(self, object_name: str, usage_data: Dict[str, List[str]]):
        """Cache usage data"""
        self.cache[object_name] = usage_data
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()
