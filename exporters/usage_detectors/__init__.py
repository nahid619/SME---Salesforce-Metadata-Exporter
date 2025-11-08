"""
Usage Detectors Package
Comprehensive field usage detection across Salesforce components

Phase 1 (Complete):
- Page Layouts (100%)
- Validation Rules (100%)
- Workflows (100%)
- Record Types (100%)
- Apex Classes (95-98%)
- Visualforce Pages (95-98%)
- Triggers (95-98%)

Phase 2 (NEW):
- Flows & Process Builder (85-90%)
- Email Templates (85-90%)
"""

from .base_detector import BaseDetector
from .layout_detector import LayoutDetector
from .validation_detector import ValidationDetector
from .workflow_detector import WorkflowDetector
from .recordtype_detector import RecordTypeDetector
from .code_search_detector import CodeSearchDetector
from .flow_detector import FlowDetector
from .email_template_detector import EmailTemplateDetector

__all__ = [
    'BaseDetector',
    'LayoutDetector',
    'ValidationDetector',
    'WorkflowDetector',
    'RecordTypeDetector',
    'CodeSearchDetector',
    'FlowDetector',
    'EmailTemplateDetector'
]