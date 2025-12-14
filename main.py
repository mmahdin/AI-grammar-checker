"""
Main controller with YAML configuration support.
Use this instead of main.py for easier configuration.
"""
import asyncio
import logging
import yaml
import sys
from pathlib import Path
from telegram_client import TelegramGrammarBot
from input_server import InputServer
from ui_window import UIManager

from qasync import QEventLoop
import signal

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GrammarCheckerApp:
    def __init__(self, config: dict):
        """Initialize the grammar checker application."""
        self.config = config
        
        telegram_config = config['telegram']
        server_config = config.get('server', {})
        
        self.telegram_bot = TelegramGrammarBot(
            api_id=telegram_config['api_id'],
            api_hash=telegram_config['api_hash'],
            bot_username=telegram_config['bot_username'],
            proxy=(telegram_config['proxy_type'], telegram_config['proxy_ip'], telegram_config['proxy_port']),
            session_name=telegram_config.get('session_name', 'grammar_checker')
            
        )
        
        self.server = InputServer(
            host=server_config.get('host', '127.0.0.1'),
            port=server_config.get('port', 8765)
        )
        
        self.ui_manager = UIManager()
        self.timeout = server_config.get('timeout', 30)
        
        self.server.set_handler(self._handle_text)
    
    async def _handle_text(self, text: str) -> dict:
        """Handle incoming text from the server."""
        try:
            logger.info(f"Processing text: {text[:50]}...")
            
            # Check grammar using Telegram bot with configured timeout
            result = await self.telegram_bot.check_grammar(text, timeout=self.timeout)
            
            # Display result in UI
            self.ui_manager.show_result(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing text: {e}")
            error_result = {
                'corrected_text': text,
                'error_analysis': [{
                    'original': text,
                    'corrected': text,
                    'explanation': f'Error: {str(e)}'
                }]
            }
            self.ui_manager.show_result(error_result)
            return error_result
    
    async def start(self):
        """Start the application."""
        logger.info("Starting Grammar Checker App...")
        
        if not self.ui_manager.app:
            self.ui_manager.initialize()
        await self.telegram_bot.start()
        await self.server.start()
        
        server_config = self.config.get('server', {})
        host = server_config.get('host', '127.0.0.1')
        port = server_config.get('port', 8765)
        
        logger.info("=" * 60)
        logger.info("Grammar Checker App is ready!")
        logger.info("=" * 60)
        logger.info(f"API Endpoint: http://{host}:{port}/check")
        logger.info(f"Bot: {self.config['telegram']['bot_username']}")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)
    
    async def stop(self):
        """Stop the application."""
        logger.info("Stopping Grammar Checker App...")
        await self.server.stop()
        await self.telegram_bot.stop()
        logger.info("Grammar Checker App stopped")
    
    async def run(self):
        """Run the application event loop."""
        await self.start()
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            await self.stop()


def load_config(config_path: str = 'config.yaml') -> dict:
    """Load configuration from YAML file."""
    config_file = Path(config_path)
    
    if not config_file.exists():
        logger.error(f"Configuration file not found: {config_path}")
        logger.info("Please create config.yaml based on config.yaml.example")
        sys.exit(1)
    
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Validate required fields
        required_fields = ['telegram']
        for field in required_fields:
            if field not in config:
                logger.error(f"Missing required field in config: {field}")
                sys.exit(1)
        
        telegram_required = ['api_id', 'api_hash', 'bot_username']
        for field in telegram_required:
            if field not in config['telegram']:
                logger.error(f"Missing required Telegram field: {field}")
                sys.exit(1)
        
        return config
        
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML config: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        sys.exit(1)



def main():
    """Entry point for running the grammar checker."""
    config = load_config()

    app_controller = GrammarCheckerApp(config)

    # Initialize UI and bind Qt + asyncio to the same event loop
    app_controller.ui_manager.initialize()
    qt_app = app_controller.ui_manager.app  # QApplication created in UIManager

    loop = QEventLoop(qt_app)
    asyncio.set_event_loop(loop)

    # Ensure Ctrl+C stops the Qt loop
    signal.signal(signal.SIGINT, lambda *args: qt_app.quit())

    async def runner():
        try:
            await app_controller.run()
        except asyncio.CancelledError:
            pass
        finally:
            # On exit, stop Telegram + server cleanly
            await app_controller.stop()

    try:
        with loop:
            loop.create_task(runner())
            loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    finally:
        # stop the loop gracefully
        loop.stop()
        if not loop.is_closed():
            loop.close()

if __name__ == "__main__":
    main()
