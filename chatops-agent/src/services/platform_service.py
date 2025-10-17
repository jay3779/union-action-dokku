"""
Platform Service

This module provides business logic for platform operations, including
NFT creation, collection management, and metadata transformation.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .enjin_client import EnjinPlatformClient

logger = logging.getLogger(__name__)


class PlatformService:
    """
    Service for managing platform operations.
    
    Handles business logic for NFT creation, collection management,
    and metadata transformation for ethical analysis workflows.
    """
    
    def __init__(self):
        """Initialize the platform service."""
        self.client = EnjinPlatformClient()
        self.collection_config = {
            "name": "Ethical Analysis Collection",
            "description": "NFTs representing ethical analysis results",
            "image_url": None
        }
        self.metadata_schema = {
            "name": "Ethical Analysis NFT",
            "description": "NFT representing ethical analysis results",
            "attributes": [
                {"trait_type": "Analysis Type", "value": "Ethical Assessment"},
                {"trait_type": "Confidence Score", "value": "0"},
                {"trait_type": "Date", "value": ""},
                {"trait_type": "Source", "value": "Union Action Workflow"}
            ]
        }
        
        logger.info("Platform service initialized")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check platform service health."""
        try:
            client_health = await self.client.health_check()
            return {
                "status": "healthy" if client_health["status"] == "healthy" else "unhealthy",
                "client": client_health,
                "service": "platform_service",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Platform service health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "service": "platform_service",
                "timestamp": datetime.now().isoformat()
            }
    
    async def create_ethical_analysis_nft(self, ethical_report: Dict[str, Any], user_address: str) -> Dict[str, Any]:
        """
        Create NFT from ethical analysis report.
        
        Args:
            ethical_report: Dictionary containing ethical analysis data
            user_address: Wallet address of the NFT owner
            
        Returns:
            Dictionary containing collection and asset information
        """
        try:
            # Transform ethical analysis to NFT metadata
            metadata = self._transform_ethical_analysis_to_metadata(ethical_report)
            
            # Create collection if not exists (or get existing)
            collection = await self._ensure_collection_exists()
            
            # Create NFT asset
            asset = await self.client.create_asset(
                collection_id=collection["collectionId"],
                metadata=metadata,
                owner_address=user_address
            )
            
            logger.info(f"Created NFT asset {asset['assetId']} for ethical analysis")
            
            return {
                "collection": collection,
                "asset": asset,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Failed to create ethical analysis NFT: {e}")
            return {
                "error": str(e),
                "status": "error"
            }
    
    async def _ensure_collection_exists(self) -> Dict[str, Any]:
        """Ensure the ethical analysis collection exists."""
        # For now, create a new collection each time
        # In production, you might want to check if collection exists first
        collection = await self.client.create_collection(
            name=self.collection_config["name"],
            description=self.collection_config["description"],
            image_url=self.collection_config["image_url"]
        )
        
        logger.info(f"Created/verified collection {collection['collectionId']}")
        return collection
    
    def _transform_ethical_analysis_to_metadata(self, ethical_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform ethical analysis report to NFT metadata.
        
        Args:
            ethical_report: Dictionary containing ethical analysis data
            
        Returns:
            Dictionary containing NFT metadata
        """
        # Extract key information from ethical report
        title = ethical_report.get("title", "Ethical Analysis Report")
        summary = ethical_report.get("summary", "Ethical analysis results")
        confidence = ethical_report.get("confidence", 0)
        date = ethical_report.get("date", datetime.now().isoformat())
        report_url = ethical_report.get("report_url", "")
        
        # Create metadata following NFT standards
        metadata = {
            "name": f"Ethical Analysis - {title}",
            "description": summary,
            "image": "",  # Could be a generated image or placeholder
            "external_url": report_url,
            "attributes": [
                {
                    "trait_type": "Analysis Type",
                    "value": "Ethical Assessment"
                },
                {
                    "trait_type": "Confidence Score",
                    "value": str(confidence)
                },
                {
                    "trait_type": "Date",
                    "value": date
                },
                {
                    "trait_type": "Source",
                    "value": "Union Action Workflow"
                },
                {
                    "trait_type": "Report ID",
                    "value": ethical_report.get("report_id", "unknown")
                }
            ]
        }
        
        # Add any additional attributes from the report
        if "additional_attributes" in ethical_report:
            metadata["attributes"].extend(ethical_report["additional_attributes"])
        
        logger.info(f"Transformed ethical analysis to metadata: {metadata['name']}")
        return metadata
    
    async def get_collection_info(self, collection_id: str) -> Dict[str, Any]:
        """Get information about a collection."""
        try:
            collection = await self.client.get_collection(collection_id)
            return {
                "collection": collection,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {
                "error": str(e),
                "status": "error"
            }
    
    async def get_asset_info(self, asset_id: str) -> Dict[str, Any]:
        """Get information about an asset."""
        try:
            asset = await self.client.get_asset(asset_id)
            return {
                "asset": asset,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Failed to get asset info: {e}")
            return {
                "error": str(e),
                "status": "error"
            }
    
    async def transfer_asset(self, asset_id: str, to_address: str, from_address: str) -> Dict[str, Any]:
        """Transfer an asset to another user."""
        try:
            result = await self.client.transfer_asset(asset_id, to_address, from_address)
            logger.info(f"Transferred asset {asset_id} to {to_address}")
            return {
                "transfer": result,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Failed to transfer asset: {e}")
            return {
                "error": str(e),
                "status": "error"
            }
    
    async def create_collection_with_config(self, name: str, description: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a collection with custom configuration."""
        try:
            collection_config = {
                "name": name,
                "description": description,
                "image_url": config.get("image_url") if config else None
            }
            
            collection = await self.client.create_collection(**collection_config)
            logger.info(f"Created collection {collection['collectionId']} with custom config")
            
            return {
                "collection": collection,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Failed to create collection with config: {e}")
            return {
                "error": str(e),
                "status": "error"
            }
