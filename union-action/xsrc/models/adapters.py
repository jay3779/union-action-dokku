"""
TransformationAdapter abstract base class.

Defines interface for all component-to-component transformation adapters.
Reference: data-model.md section 2 (TransformationAdapter)
"""

from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from typing import Any


class TransformationAdapter(ABC, BaseModel):
    """
    Abstract base class for transformation adapters.
    
    All adapters must implement transform() and validate() methods.
    Constitutional Compliance: Type-safe validation at every boundary.
    """
    
    source_schema: str = Field(
        ..., 
        description="Source schema name and version (e.g., 'NHSComplaintDocument_v1')"
    )
    target_schema: str = Field(
        ..., 
        description="Target schema name and version (e.g., 'CaseBuilder_v1')"
    )
    pydantic_ai_enabled: bool = Field(
        default=False, 
        description="Whether Pydantic AI is used for schema adaptation"
    )
    
    @abstractmethod
    def transform(self, source_data: Any) -> Any:
        """
        Transform source data to target schema.
        
        Args:
            source_data: Source Pydantic model instance
        
        Returns:
            Target Pydantic model instance
        
        Raises:
            ValidationError: If source data fails validation
            ValueError: If transformation logic fails
        """
        pass
    
    @abstractmethod
    def validate(self, source_data: Any) -> bool:
        """
        Validate source data against source schema.
        
        Args:
            source_data: Source Pydantic model instance
        
        Returns:
            True if validation passes
        
        Raises:
            ValidationError: If validation fails
        """
        pass
    
    class Config:
        arbitrary_types_allowed = True

