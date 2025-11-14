"""
SME - System Health Check
Checks system resources before starting heavy operations
"""
import psutil
from typing import Tuple, Dict
from config.logger import get_logger

logger = get_logger('HealthCheck')


class SystemHealthChecker:
    """Check system health before operations"""
    
    @staticmethod
    def check_system_health() -> Tuple[bool, str, Dict]:
        """
        Check if system can handle export operations
        
        Returns:
            (is_healthy, message, metrics)
        """
        metrics = {}
        warnings = []
        
        # Check memory
        memory = psutil.virtual_memory()
        metrics['memory_total_gb'] = round(memory.total / (1024**3), 2)
        metrics['memory_available_gb'] = round(memory.available / (1024**3), 2)
        metrics['memory_percent'] = memory.percent
        
        if memory.percent > 90:
            return False, "❌ Low memory available (>90% used). Close other applications before continuing.", metrics
        elif memory.percent > 80:
            warnings.append(f"⚠️ High memory usage ({memory.percent}%)")
        
        # Check disk space
        disk = psutil.disk_usage('/')
        metrics['disk_total_gb'] = round(disk.total / (1024**3), 2)
        metrics['disk_free_gb'] = round(disk.free / (1024**3), 2)
        metrics['disk_percent'] = disk.percent
        
        if disk.percent > 95:
            return False, f"❌ Low disk space (only {metrics['disk_free_gb']}GB free). Free up space before continuing.", metrics
        elif disk.percent > 90:
            warnings.append(f"⚠️ Low disk space ({metrics['disk_free_gb']}GB free)")
        
        # Check CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        metrics['cpu_percent'] = cpu_percent
        
        if cpu_percent > 90:
            warnings.append(f"⚠️ High CPU usage ({cpu_percent}%)")
        
        # Log metrics
        logger.info("System Health Check:")
        logger.info(f"  Memory: {metrics['memory_available_gb']}GB available ({metrics['memory_percent']}% used)")
        logger.info(f"  Disk: {metrics['disk_free_gb']}GB free ({metrics['disk_percent']}% used)")
        logger.info(f"  CPU: {metrics['cpu_percent']}% usage")
        
        # Return result
        if warnings:
            message = "✅ System healthy (with warnings):\n" + "\n".join(warnings)
        else:
            message = "✅ System healthy - Ready for operations"
        
        return True, message, metrics
    
    @staticmethod
    def estimate_export_memory(object_count: int, include_usage: bool = False) -> float:
        """
        Estimate memory needed for export
        
        Args:
            object_count: Number of objects to export
            include_usage: Whether usage analysis is enabled
            
        Returns:
            Estimated memory in GB
        """
        # Base memory: ~50MB
        base_memory = 0.05
        
        # Per object: ~5MB without usage, ~15MB with usage
        per_object = 0.015 if include_usage else 0.005
        
        # Code cache: ~100MB if usage enabled
        code_cache = 0.1 if include_usage else 0
        
        total = base_memory + (object_count * per_object) + code_cache
        
        return round(total, 2)
    
    @staticmethod
    def can_handle_export(object_count: int, include_usage: bool = False) -> Tuple[bool, str]:
        """
        Check if system can handle the requested export
        
        Returns:
            (can_handle, message)
        """
        is_healthy, health_message, metrics = SystemHealthChecker.check_system_health()
        
        if not is_healthy:
            return False, health_message
        
        # Estimate memory needed
        estimated_memory = SystemHealthChecker.estimate_export_memory(object_count, include_usage)
        available_memory = metrics['memory_available_gb']
        
        if estimated_memory > available_memory * 0.8:  # Need 80% of available memory
            return False, (
                f"⚠️ Insufficient memory for this export.\n\n"
                f"Estimated need: {estimated_memory}GB\n"
                f"Available: {available_memory}GB\n\n"
                f"Suggestions:\n"
                f"• Export fewer objects at a time\n"
                f"• Disable usage analysis\n"
                f"• Close other applications"
            )
        
        return True, f"✅ System can handle export (estimated {estimated_memory}GB needed)"


def check_before_export(object_count: int, include_usage: bool = False) -> bool:
    """
    Convenience function to check before export with user prompt
    
    Returns:
        True if should proceed, False if should cancel
    """
    from tkinter import messagebox
    
    can_handle, message = SystemHealthChecker.can_handle_export(object_count, include_usage)
    
    if not can_handle:
        result = messagebox.askyesno(
            "System Resources Warning",
            f"{message}\n\nContinue anyway?",
            icon='warning'
        )
        return result
    
    return True