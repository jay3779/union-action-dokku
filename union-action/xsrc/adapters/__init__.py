"""
Transformation adapters for Union Action Workflow Integration.

Component-to-component data transformation with Pydantic validation.
"""

from .complaint_to_kantian import ComplaintToKantianAdapter
from .kantian_to_koers import KantianToKOERSAdapter, ViolationToModuleMapper

__all__ = ["ComplaintToKantianAdapter", "KantianToKOERSAdapter", "ViolationToModuleMapper"]

