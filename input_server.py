"""
Input server module for receiving text from the system (via HTTP API).
Using HTTP instead of sockets for better cross-platform compatibility.
"""
import asyncio
from aiohttp import web
import logging
from typing import Callable, Awaitable, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InputServer:
    def __init__(self, host: str = '127.0.0.1', port: int = 8765):
        """
        Initialize HTTP server for receiving text input.
        
        Args:
            host: Server host address
            port: Server port
        """
        self.host = host
        self.port = port
        self.app = web.Application()
        self.runner: Optional[web.AppRunner] = None
        self.text_handler: Optional[Callable[[str], Awaitable[dict]]] = None
        
        # Setup routes
        self.app.router.add_post('/check', self._handle_check)
        self.app.router.add_get('/health', self._handle_health)
    
    def set_handler(self, handler: Callable[[str], Awaitable[dict]]):
        """Set the handler function for processing text."""
        self.text_handler = handler
    
    async def start(self):
        """Start the HTTP server."""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.host, self.port)
        await site.start()
        logger.info(f"Input server started on http://{self.host}:{self.port}")
    
    async def stop(self):
        """Stop the HTTP server."""
        if self.runner:
            await self.runner.cleanup()
            logger.info("Input server stopped")
    
    async def _handle_check(self, request: web.Request) -> web.Response:
        """Handle grammar check requests."""
        try:
            data = await request.json()
            text = data.get('text', '')
            
            if not text:
                return web.json_response(
                    {'error': 'No text provided'},
                    status=400
                )
            
            if not self.text_handler:
                return web.json_response(
                    {'error': 'Handler not configured'},
                    status=500
                )
            
            # Process text with the handler
            result = await self.text_handler(text)
            return web.json_response(result)
            
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return web.json_response(
                {'error': str(e)},
                status=500
            )
    
    async def _handle_health(self, request: web.Request) -> web.Response:
        """Health check endpoint."""
        return web.json_response({'status': 'ok'})