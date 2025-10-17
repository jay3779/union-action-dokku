"""
Platform Data Models

This module defines Pydantic models for platform integration,
including NFT collections, assets, and workflow tracking.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator


class EnjinPlatformClient(BaseModel):
    """Model for Enjin Platform client configuration."""
    
    api_url: str = Field(..., description="Platform API endpoint")
    auth_token: str = Field(..., description="Platform authentication token")
    testnet_mode: bool = Field(default=True, description="Whether using testnet environment")
    rate_limit_config: Dict[str, Any] = Field(default_factory=dict, description="API rate limiting configuration")
    
    @validator('api_url')
    def validate_api_url(cls, v):
        """Validate API URL format."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('API URL must start with http:// or https://')
        return v
    
    @validator('auth_token')
    def validate_auth_token(cls, v):
        """Validate auth token is not empty."""
        if not v or len(v.strip()) == 0:
            raise ValueError('Auth token cannot be empty')
        return v


class PlatformService(BaseModel):
    """Model for platform service configuration."""
    
    client: EnjinPlatformClient = Field(..., description="Platform API client")
    collection_config: Dict[str, Any] = Field(default_factory=dict, description="Collection creation configuration")
    metadata_schema: Dict[str, Any] = Field(default_factory=dict, description="NFT metadata schema definition")


class NFTCollection(BaseModel):
    """Model for NFT collection."""
    
    collection_id: str = Field(..., description="Platform collection identifier")
    name: str = Field(..., description="Collection name")
    description: str = Field(..., description="Collection description")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Collection metadata")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    platform_url: str = Field(..., description="Platform collection URL")
    
    @validator('collection_id')
    def validate_collection_id(cls, v):
        """Validate collection ID is not empty."""
        if not v or len(v.strip()) == 0:
            raise ValueError('Collection ID cannot be empty')
        return v
    
    @validator('name')
    def validate_name(cls, v):
        """Validate collection name is not empty."""
        if not v or len(v.strip()) == 0:
            raise ValueError('Collection name cannot be empty')
        return v


class NFTAsset(BaseModel):
    """Model for NFT asset."""
    
    asset_id: str = Field(..., description="Platform asset identifier")
    collection_id: str = Field(..., description="Parent collection identifier")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Asset metadata (ethical analysis data)")
    owner_address: str = Field(..., description="Current owner wallet address")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    platform_url: str = Field(..., description="Platform asset URL")
    
    @validator('asset_id')
    def validate_asset_id(cls, v):
        """Validate asset ID is not empty."""
        if not v or len(v.strip()) == 0:
            raise ValueError('Asset ID cannot be empty')
        return v
    
    @validator('collection_id')
    def validate_collection_id(cls, v):
        """Validate collection ID is not empty."""
        if not v or len(v.strip()) == 0:
            raise ValueError('Collection ID cannot be empty')
        return v
    
    @validator('owner_address')
    def validate_owner_address(cls, v):
        """Validate owner address format."""
        if not v or len(v.strip()) == 0:
            raise ValueError('Owner address cannot be empty')
        # Basic wallet address validation (could be enhanced)
        if len(v) < 10:
            raise ValueError('Owner address appears to be too short')
        return v


class PlatformWorkflow(BaseModel):
    """Model for platform workflow tracking."""
    
    workflow_id: str = Field(..., description="Existing workflow identifier")
    platform_operations: List[str] = Field(default_factory=list, description="Platform operations performed")
    nft_assets: List[NFTAsset] = Field(default_factory=list, description="Created NFT assets")
    collection_id: Optional[str] = Field(None, description="Associated collection")
    status: str = Field(default="initialized", description="Platform operation status")
    error_details: Dict[str, Any] = Field(default_factory=dict, description="Platform operation errors")
    
    @validator('status')
    def validate_status(cls, v):
        """Validate status is one of allowed values."""
        allowed_statuses = [
            "initialized", "collection_created", "assets_created", 
            "distribution_complete", "error", "completed"
        ]
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return v


class WebhookRequest(BaseModel):
    """Extended webhook request model with platform integration."""
    
    from_number: str = Field(..., description="WhatsApp sender number")
    body: str = Field(..., description="Message content")
    timestamp: int = Field(..., description="Message timestamp")
    platform_enabled: bool = Field(default=False, description="Whether platform integration is enabled")
    platform_config: Dict[str, Any] = Field(default_factory=dict, description="Platform-specific configuration")
    user_address: Optional[str] = Field(None, description="User wallet address for NFT creation")


class WebhookResponse(BaseModel):
    """Extended webhook response model with platform data."""
    
    status: str = Field(..., description="Response status")
    message: str = Field(..., description="Response message")
    platform_assets: List[NFTAsset] = Field(default_factory=list, description="Created platform assets")
    platform_collection: Optional[NFTCollection] = Field(None, description="Associated collection")
    platform_errors: List[str] = Field(default_factory=list, description="Platform operation errors")
    
    @validator('status')
    def validate_status(cls, v):
        """Validate status is success or error."""
        if v not in ["success", "error"]:
            raise ValueError('Status must be "success" or "error"')
        return v


class EthicalAnalysisReport(BaseModel):
    """Extended ethical analysis report with platform metadata."""
    
    report_id: str = Field(..., description="Report identifier")
    title: str = Field(..., description="Report title")
    summary: str = Field(..., description="Report summary")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    date: datetime = Field(default_factory=datetime.now, description="Report date")
    report_url: Optional[str] = Field(None, description="Report URL")
    platform_metadata: Dict[str, Any] = Field(default_factory=dict, description="Platform-specific metadata")
    nft_asset_id: Optional[str] = Field(None, description="Associated NFT asset identifier")
    collection_id: Optional[str] = Field(None, description="Associated collection identifier")


class DeploymentReport(BaseModel):
    """Extended deployment report with platform assets."""
    
    deployment_id: str = Field(..., description="Deployment identifier")
    status: str = Field(..., description="Deployment status")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    platform_assets: List[NFTAsset] = Field(default_factory=list, description="Created platform assets")
    platform_collection: Optional[NFTCollection] = Field(None, description="Associated collection")
    platform_status: str = Field(default="pending", description="Platform operation status")
    
    @validator('status')
    def validate_status(cls, v):
        """Validate deployment status."""
        allowed_statuses = ["pending", "in_progress", "completed", "failed"]
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return v


class PlatformHealthResponse(BaseModel):
    """Model for platform health check response."""
    
    status: str = Field(..., description="Health status")
    platform: Dict[str, Any] = Field(..., description="Platform information")
    timestamp: datetime = Field(default_factory=datetime.now, description="Check timestamp")
    
    @validator('status')
    def validate_status(cls, v):
        """Validate health status."""
        if v not in ["healthy", "unhealthy"]:
            raise ValueError('Status must be "healthy" or "unhealthy"')
        return v


class CreateCollectionRequest(BaseModel):
    """Model for collection creation request."""
    
    name: str = Field(..., description="Collection name")
    description: str = Field(..., description="Collection description")
    image_url: Optional[str] = Field(None, description="Collection image URL")
    external_url: Optional[str] = Field(None, description="External collection URL")
    attributes: List[Dict[str, str]] = Field(default_factory=list, description="Collection attributes")


class CreateAssetRequest(BaseModel):
    """Model for asset creation request."""
    
    collection_id: str = Field(..., description="Parent collection ID")
    metadata: Dict[str, Any] = Field(..., description="Asset metadata")
    owner_address: str = Field(..., description="Owner wallet address")


class TransferAssetRequest(BaseModel):
    """Model for asset transfer request."""
    
    to_address: str = Field(..., description="Recipient wallet address")
    from_address: str = Field(..., description="Sender wallet address")
    
    @validator('to_address')
    def validate_to_address(cls, v):
        """Validate recipient address."""
        if not v or len(v.strip()) == 0:
            raise ValueError('Recipient address cannot be empty')
        return v
    
    @validator('from_address')
    def validate_from_address(cls, v):
        """Validate sender address."""
        if not v or len(v.strip()) == 0:
            raise ValueError('Sender address cannot be empty')
        return v
