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
        return f"""You are an English-language teacher and translator.

            First, detect the input language:
            - If the input is **Persian (Farsi)**: translate it to natural, correct **English** and respond with **ONLY** the JSON format below (no extra keys). In this case, set "error_analysis" to an empty array [].
            - If the input is **English**: correct grammar, spelling, punctuation, and phrasing, and then explain the corrections with grammar rules. Also provide a **Persian translation of the corrected English**.

            For English input, your job is to:
            1. Provide the corrected English sentence/text as "corrected_text".
            2. Provide the Persian translation of "corrected_text" as "persian_translation".
            3. Explain each correction in "error_analysis", showing:
            - the incorrect part ("original"),
            - the corrected part ("corrected"),
            - a short, clear explanation ("explanation") that includes the **grammar rule** (name the rule and briefly state it), plus a minimal example if helpful.

            Guidelines for explanations:
            - Be concise but more grammar-focused than usual.
            - Use clear rule names (e.g., Subject–Verb Agreement, Articles (a/an/the), Tense consistency, Prepositions, Word order, Countable vs. uncountable nouns, Parallel structure, Punctuation, Collocations).
            - Prefer 1–3 sentences per explanation; avoid long lectures.
            - If nothing is wrong, still return the JSON, with "error_analysis": [].

            Your entire response must:
            * Start with: **RESPONSE:**
            * Contain **only valid JSON** after that (no markdown, no backticks)
            * Use the exact structure below (always include all keys):

            {{
            "corrected_text": "...",
            "persian_translation": "...",
            "error_analysis": [
                {{
                "original": "...",
                "corrected": "...",
                "explanation": "..."
                }}
            ]
            }}

            Here is the text:
            {text}"""


    
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
