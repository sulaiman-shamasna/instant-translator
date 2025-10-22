import asyncio
import websockets
import sounddevice as sd
import numpy as np
import json
import logging
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioTranslatorClient:
    def __init__(self, websocket_url="ws://localhost:8010/audio"):
        self.websocket_url = websocket_url
        self.websocket = None
        self.is_recording = False
        self.audio_queue = asyncio.Queue()
        
        # Audio configuration
        self.sample_rate = int(os.getenv("SAMPLE_RATE", 16000))
        self.chunk_size = int(os.getenv("CHUNK_SIZE", 1024))
        
    def audio_callback(self, indata: np.ndarray, frames: int, time: float, status: int) -> None:
        """Callback for sounddevice to process audio chunks."""
        if status:
            logger.warning(f"Audio callback status: {status}")
        
        if self.is_recording:
            # Convert to float32 and put in queue
            audio_data = indata.copy().astype(np.float32)
            try:
                self.audio_queue.put_nowait(audio_data.tobytes())
            except asyncio.QueueFull:
                logger.warning("Audio queue is full, dropping audio chunk")
    
    async def connect_to_server(self):
        """Connect to the WebSocket server"""
        try:
            print(f"🔄 Connecting to server at {self.websocket_url}...")
            self.websocket = await websockets.connect(self.websocket_url)
            print("✅ Connected to translation server successfully!")
            logger.info("Connected to translation server")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to server: {e}")
            print("💡 Make sure the server is running on the correct port (8010)")
            logger.error(f"Failed to connect to server: {e}")
            return False
    
    async def send_audio_data(self):
        """Send audio data to the server"""
        try:
            while self.is_recording:
                try:
                    # Wait for audio data with timeout
                    audio_data = await asyncio.wait_for(
                        self.audio_queue.get(), 
                        timeout=1.0
                    )
                    
                    if self.websocket:
                        try:
                            await self.websocket.send(audio_data)
                        except websockets.exceptions.ConnectionClosed:
                            logger.info("Connection closed, stopping audio send")
                            break
                    
                except asyncio.TimeoutError:
                    continue
                except asyncio.CancelledError:
                    logger.info("Audio sending cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error sending audio data: {e}")
                    break
                    
        except asyncio.CancelledError:
            logger.info("Audio sending task cancelled")
        except Exception as e:
            logger.error(f"Error in send_audio_data: {e}")
    
    async def receive_translations(self):
        """Receive and display translations from the server"""
        try:
            while self.websocket:
                try:
                    message = await self.websocket.recv()
                    
                    if isinstance(message, str):
                        # Parse JSON response
                        try:
                            result = json.loads(message)
                            self.display_translation(result)
                        except json.JSONDecodeError:
                            logger.warning(f"Received non-JSON message: {message}")
                    
                except websockets.exceptions.ConnectionClosed:
                    logger.info("Connection to server closed")
                    break
                except asyncio.CancelledError:
                    logger.info("Translation receiving cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error receiving message: {e}")
                    break
                    
        except asyncio.CancelledError:
            logger.info("Translation receiving task cancelled")
        except Exception as e:
            logger.error(f"Error in receive_translations: {e}")
    
    def display_translation(self, result: dict):
        """Display the translation result"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        print(f"\n{'='*60}")
        print(f"[{timestamp}] Translation Result:")
        print(f"{'='*60}")
        print(f"Original: {result.get('original', 'N/A')}")
        print(f"Translation: {result.get('translation', 'N/A')}")
        print(f"{'='*60}\n")
    
    async def start_recording(self):
        """Start recording audio and processing"""
        if not await self.connect_to_server():
            return
        
        self.is_recording = True
        
        try:
            # Start audio input stream
            with sd.InputStream(
                callback=self.audio_callback,
                blocksize=self.chunk_size,
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32
            ):
                print("🎤 Audio recording started. Speak into your microphone...")
                print("⏹️  Press Ctrl+C to stop recording")
                logger.info("Audio recording started. Speak into your microphone...")
                logger.info("Press Ctrl+C to stop recording")
                
                # Run audio sending and receiving concurrently
                try:
                    await asyncio.gather(
                        self.send_audio_data(),
                        self.receive_translations()
                    )
                except asyncio.CancelledError:
                    logger.info("Recording tasks cancelled")
                
        except KeyboardInterrupt:
            logger.info("Recording stopped by user")
        except Exception as e:
            logger.error(f"Error during recording: {e}")
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up resources"""
        self.is_recording = False
        
        if self.websocket:
            try:
                await self.websocket.close()
                logger.info("Disconnected from server")
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")

async def main():
    """Main function to run the audio translator client"""
    print("🎤 Instant Audio Translator Client")
    print("=" * 50)
    print("This client will:")
    print("1. Record audio from your microphone")
    print("2. Send it to the translation server")
    print("3. Display real-time translations")
    print("=" * 50)
    
    # Get server URL from environment or use default
    server_url = os.getenv("SERVER_URL", "ws://localhost:8010/audio")
    
    client = AudioTranslatorClient(server_url)
    
    try:
        await client.start_recording()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    asyncio.run(main())