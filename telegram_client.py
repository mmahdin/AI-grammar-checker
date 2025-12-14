"""
Telegram client module for interacting with AI bots via Telethon.
"""
import asyncio
import json
import re
from telethon import TelegramClient, events
from typing import Optional, Callable
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramGrammarBot:
    def __init__(self, api_id: int, api_hash: str, bot_username: str, proxy: tuple, session_name: str = "grammar_checker"):
        """
        Initialize Telegram client for grammar checking.
        
        Args:
            api_id: Telegram API ID (get from my.telegram.org)
            api_hash: Telegram API hash
            bot_username: Username of the AI bot (e.g., '@ChatGPTbot')
            session_name: Session file name
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.bot_username = bot_username
        self.session_name = session_name
        self.client: Optional[TelegramClient] = None
        self.response_queue = asyncio.Queue()
        self.proxy = proxy
        
    async def start(self):
        """Initialize and start the Telegram client."""
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash, proxy=self.proxy)
        await self.client.start()
        logger.info("Telegram client started successfully")
        
        # Register message handler
        @self.client.on(events.NewMessage(from_users=self.bot_username))
        async def handler(event):
            message_text = event.message.message
            if message_text.startswith("RESPONSE:"):
                await self.response_queue.put(message_text)
                
    async def stop(self):
        """Stop the Telegram client."""
        if self.client:
            await self.client.disconnect()
            logger.info("Telegram client stopped")
    
    async def check_grammar(self, text: str, timeout: int = 30) -> dict:
        """
        Send text to AI bot and wait for grammar analysis response.
        
        Args:
            text: English text to check
            timeout: Maximum time to wait for response (seconds)
            
        Returns:
            Parsed JSON response from the bot
        """
        prompt = self._build_prompt(text)
        
        # Clear any pending responses
        while not self.response_queue.empty():
            await self.response_queue.get()
        
        # Send message to bot
        await self.client.send_message(self.bot_username, prompt)
        logger.info(f"Sent text to {self.bot_username}")
        
        # Wait for response
        try:
            response = await asyncio.wait_for(
                self.response_queue.get(), 
                timeout=timeout
            )
            return self._parse_response(response)
        except asyncio.TimeoutError:
            logger.error("Timeout waiting for bot response")
            raise Exception("Bot did not respond in time")
    
    def _build_prompt(self, text: str) -> str:
        """Build the full prompt with the user's text inserted."""
        return f"""You are an English-language teacher. When I send you a sentence or short text in English, your job is to:
                    1. Correct all grammar, spelling, and phrasing errors.
                    2. Provide the corrected version of the sentence at the top.
                    3. Then explain **where my sentence was wrong**, showing the incorrect parts and their correct forms.
                    4. Explain **the grammar rules** behind each correction (e.g., when to use present perfect, how to form a question, word order, article usage, etc.).
                    5. Keep your explanations **short, structured, and clear** — avoid unnecessary details.
                    6. Analyze the sentence based on the meaning I intended, and explain how correct English grammar should express that meaning.

                    Your entire response must:
                    * Start with: **RESPONSE:**
                    * Contain **only valid JSON** after that
                    * Use the exact structure below:

                    ```json
                    {{
                    "corrected_text": "...",
                    "error_analysis": [
                        {{
                        "original": "...",
                        "corrected": "...",
                        "explanation": "..."
                        }}
                    ]
                    }}
                    ```

                    Here is the text you should analyze and correct:
                    ```
                    {text}
                    ```"""
    
    def _parse_response(self, response: str) -> dict:
        """Parse the bot's response and extract JSON."""
        # Remove "RESPONSE:" prefix
        json_text = response[len("RESPONSE:"):].strip()
        
        # Remove markdown code blocks if present
        json_text = re.sub(r'^```json\s*', '', json_text)
        json_text = re.sub(r'\s*```$', '', json_text)
        json_text = json_text.strip()
        
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.error(f"Response was: {json_text}")
            raise Exception("Invalid JSON response from bot")
