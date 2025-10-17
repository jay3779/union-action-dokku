"""
Enjin Platform API Client

This module provides the core client for communicating with the Enjin Platform API.
It handles authentication, rate limiting, and GraphQL operations.
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

import httpx
from gql import gql, Client
from gql.transport.httpx import HTTPXTransport
from gql.transport.exceptions import TransportError

logger = logging.getLogger(__name__)


class EnjinPlatformClient:
    """
    Client for interacting with the Enjin Platform API.
    
    Handles GraphQL operations, authentication, rate limiting, and error handling.
    """
    
    def __init__(self):
        """Initialize the Enjin Platform client."""
        self.api_url = os.getenv("ENJIN_PLATFORM_API_URL", "https://platform.enjin.io/graphql")
        self.api_key = os.getenv("ENJIN_PLATFORM_API_KEY")
        self.testnet_mode = os.getenv("ENJIN_TESTNET_MODE", "true").lower() == "true"
        
        # Rate limiting configuration
        self.rate_limit_config = {
            "requests_per_minute": int(os.getenv("PLATFORM_RATE_LIMIT_REQUESTS_PER_MINUTE", "60")),
            "burst_limit": int(os.getenv("PLATFORM_RATE_LIMIT_BURST", "10")),
            "retry_attempts": int(os.getenv("PLATFORM_RETRY_ATTEMPTS", "3")),
            "retry_delay": float(os.getenv("PLATFORM_RETRY_DELAY", "1.0"))
        }
        
        # Request tracking for rate limiting
        self.request_times: List[datetime] = []
        self.burst_requests = 0
        self.last_burst_reset = datetime.now()
        
        # Initialize GraphQL client
        self._setup_client()
    
    def _setup_client(self):
        """Set up the GraphQL client with authentication."""
        if not self.api_key:
            raise ValueError("ENJIN_PLATFORM_API_KEY environment variable is required")
        
        # Configure HTTP transport with authentication
        transport = HTTPXTransport(
            url=self.api_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Union-Action-Chatops-Agent/1.0"
            },
            timeout=30.0
        )
        
        # Create GraphQL client
        self.client = Client(
            transport=transport,
            fetch_schema_from_transport=True
        )
        
        logger.info(f"Enjin Platform client initialized for {'testnet' if self.testnet_mode else 'mainnet'}")
    
    async def _check_rate_limit(self):
        """Check and enforce rate limiting."""
        now = datetime.now()
        
        # Clean old request times (older than 1 minute)
        self.request_times = [req_time for req_time in self.request_times 
                             if now - req_time < timedelta(minutes=1)]
        
        # Check burst limit
        if now - self.last_burst_reset > timedelta(minutes=1):
            self.burst_requests = 0
            self.last_burst_reset = now
        
        # Enforce rate limits
        if len(self.request_times) >= self.rate_limit_config["requests_per_minute"]:
            sleep_time = 60 - (now - self.request_times[0]).total_seconds()
            if sleep_time > 0:
                logger.warning(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                await asyncio.sleep(sleep_time)
        
        if self.burst_requests >= self.rate_limit_config["burst_limit"]:
            sleep_time = 60 - (now - self.last_burst_reset).total_seconds()
            if sleep_time > 0:
                logger.warning(f"Burst limit reached, sleeping for {sleep_time:.2f} seconds")
                await asyncio.sleep(sleep_time)
        
        # Record this request
        self.request_times.append(now)
        self.burst_requests += 1
    
    async def _execute_with_retry(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute GraphQL query with retry logic."""
        for attempt in range(self.rate_limit_config["retry_attempts"]):
            try:
                await self._check_rate_limit()
                
                result = await self.client.execute_async(
                    gql(query),
                    variable_values=variables or {}
                )
                
                return result
                
            except TransportError as e:
                logger.warning(f"Transport error on attempt {attempt + 1}: {e}")
                if attempt < self.rate_limit_config["retry_attempts"] - 1:
                    await asyncio.sleep(self.rate_limit_config["retry_delay"] * (2 ** attempt))
                else:
                    raise
            except Exception as e:
                logger.error(f"Unexpected error executing query: {e}")
                raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Check platform API health."""
        query = """
        query HealthCheck {
            __schema {
                types {
                    name
                }
            }
        }
        """
        
        try:
            result = await self._execute_with_retry(query)
            return {
                "status": "healthy",
                "api_url": self.api_url,
                "testnet_mode": self.testnet_mode,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "api_url": self.api_url,
                "testnet_mode": self.testnet_mode,
                "timestamp": datetime.now().isoformat()
            }
    
    async def create_collection(self, name: str, description: str, image_url: Optional[str] = None) -> Dict[str, Any]:
        """Create a new NFT collection."""
        mutation = """
        mutation CreateCollection($input: CreateCollectionInput!) {
            createCollection(input: $input) {
                collectionId
                name
                description
                metadata
                createdAt
                platformUrl
            }
        }
        """
        
        variables = {
            "input": {
                "name": name,
                "description": description,
                "imageUrl": image_url
            }
        }
        
        result = await self._execute_with_retry(mutation, variables)
        return result["createCollection"]
    
    async def create_asset(self, collection_id: str, metadata: Dict[str, Any], owner_address: str) -> Dict[str, Any]:
        """Create a new NFT asset."""
        mutation = """
        mutation CreateAsset($input: CreateAssetInput!) {
            createAsset(input: $input) {
                assetId
                collectionId
                metadata
                ownerAddress
                createdAt
                platformUrl
            }
        }
        """
        
        variables = {
            "input": {
                "collectionId": collection_id,
                "metadata": metadata,
                "ownerAddress": owner_address
            }
        }
        
        result = await self._execute_with_retry(mutation, variables)
        return result["createAsset"]
    
    async def transfer_asset(self, asset_id: str, to_address: str, from_address: str) -> Dict[str, Any]:
        """Transfer an NFT asset."""
        mutation = """
        mutation TransferAsset($input: TransferAssetInput!) {
            transferAsset(input: $input) {
                assetId
                ownerAddress
                platformUrl
            }
        }
        """
        
        variables = {
            "input": {
                "assetId": asset_id,
                "toAddress": to_address,
                "fromAddress": from_address
            }
        }
        
        result = await self._execute_with_retry(mutation, variables)
        return result["transferAsset"]
    
    async def get_collection(self, collection_id: str) -> Dict[str, Any]:
        """Get collection details."""
        query = """
        query GetCollection($collectionId: String!) {
            getCollection(collectionId: $collectionId) {
                collectionId
                name
                description
                metadata
                createdAt
                platformUrl
                assets {
                    assetId
                    metadata
                    ownerAddress
                }
            }
        }
        """
        
        variables = {"collectionId": collection_id}
        result = await self._execute_with_retry(query, variables)
        return result["getCollection"]
    
    async def get_asset(self, asset_id: str) -> Dict[str, Any]:
        """Get asset details."""
        query = """
        query GetAsset($assetId: String!) {
            getAsset(assetId: $assetId) {
                assetId
                collectionId
                metadata
                ownerAddress
                createdAt
                platformUrl
            }
        }
        """
        
        variables = {"assetId": asset_id}
        result = await self._execute_with_retry(query, variables)
        return result["getAsset"]
