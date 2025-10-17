"""
Chatops Agent main module.

This module provides the entry point for the chatops-agent process
that communicates with the union-action API via localhost.
"""

import asyncio
import logging
import sys
from typing import Optional

import httpx
import structlog

from .config import Config
from .services.union_action_client import UnionActionClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = structlog.get_logger(__name__)


class ChatopsAgent:
    """Main chatops agent class."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the chatops agent."""
        self.config = config or Config()
        self.client = UnionActionClient(
            base_url=self.config.union_action_url,
            timeout=self.config.request_timeout
        )
        self.running = False
    
    async def start(self):
        """Start the chatops agent."""
        logger.info("Starting chatops agent", version=__version__)
        self.running = True
        
        try:
            # Verify union-action API is available
            await self.client.health_check()
            logger.info("Union-action API is healthy")
            
            # Start main processing loop
            await self._main_loop()
            
        except Exception as e:
            logger.error("Chatops agent error", error=str(e))
            raise
        finally:
            self.running = False
            logger.info("Chatops agent stopped")
    
    async def stop(self):
        """Stop the chatops agent."""
        logger.info("Stopping chatops agent")
        self.running = False
    
    async def _main_loop(self):
        """Main processing loop."""
        while self.running:
            try:
                # Check union-action API health
                health_status = await self.client.health_check()
                logger.debug("Health check", status=health_status)
                
                # Process any pending requests
                # This is where the actual chatops logic would go
                await asyncio.sleep(self.config.poll_interval)
                
            except Exception as e:
                logger.error("Error in main loop", error=str(e))
                await asyncio.sleep(self.config.error_retry_interval)


async def main():
    """Main entry point."""
    try:
        config = Config()
        agent = ChatopsAgent(config)
        
        # Handle graceful shutdown
        def signal_handler():
            logger.info("Received shutdown signal")
            asyncio.create_task(agent.stop())
        
        # Start the agent
        await agent.start()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error("Fatal error", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
