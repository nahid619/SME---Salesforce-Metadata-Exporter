"""
SME - Helper utility functions
"""
from datetime import datetime, timedelta
from typing import Dict


def format_runtime(seconds: float) -> str:
    """
    Format runtime in HH:MM:SS format
    
    Args:
        seconds: Runtime in seconds
        
    Returns:
        Formatted string (e.g., "01:23:45")
    """
    td = timedelta(seconds=int(seconds))
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def get_timestamp() -> str:
    """
    Get current timestamp for logging
    
    Returns:
        Formatted timestamp string [HH:MM:SS]
    """
    return datetime.now().strftime("[%H:%M:%S]")


def format_file_timestamp() -> str:
    """
    Get timestamp for file naming
    
    Returns:
        Formatted timestamp string (YYYYMMDD_HHMMSS)
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def print_statistics(stats: Dict, runtime_formatted: str, output_file: str):
    """
    Print comprehensive export statistics to console
    
    Args:
        stats: Dictionary containing export statistics
        runtime_formatted: Formatted runtime string
        output_file: Path to output file
    """
    print("\n" + "=" * 70)
    print("✅ EXPORT COMPLETED!" if not stats.get('cancelled') else "🛑 EXPORT CANCELLED!")
    print("=" * 70)
    print(f"Total Runtime: {runtime_formatted}")
    print(f"API Calls Made: {stats.get('api_calls_made', 0)}")
    print(f"Total Objects in List:          {stats['total_objects']}")
    print(f"✅ Successfully Processed:       {stats['successful_objects']}")
    print(f"❌ Failed to Process:            {stats['failed_objects']}")
    print(f"⚠️  Objects Not Found in Org:    {stats['objects_not_found']}")
    print(f"Total Picklist Fields:          {stats['total_picklist_fields']}")
    print(f"Total Picklist Values:          {stats['total_values']}")
    print(f"✅ Active Values:                {stats['total_active_values']}")
    print(f"❌ Inactive Values:              {stats['total_inactive_values']}")
    print(f"Output File: {output_file}")
    
    if stats['failed_objects'] > 0:
        print("\n❌ FAILED OBJECTS (REASONS):")
        for detail in stats['failed_object_details']:
            print(f"   • {detail['name']}: {detail['reason']}")
    
    print("=" * 70)