from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
import numpy as np
import uvicorn
import openai
import os
import io
import wave
import asyncio
import logging
from dotenv import load_dotenv
from typing import Dict, Any
import json

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

class ConnectionManager:
    def __init__(self):
        self.active_connections: set[WebSocket] = set()
        self.audio_buffer: Dict[WebSocket, bytes] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        self.audio_buffer[websocket] = b""
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.audio_buffer:
            del self.audio_buffer[websocket]
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        """Broadcast text message to all connected clients"""
        for connection in self.active_connections:
            if connection.client_state == WebSocketState.CONNECTED:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to client: {e}")

    def add_audio_chunk(self, websocket: WebSocket, audio_data: bytes):
        """Add audio chunk to buffer for a specific client"""
        if websocket in self.audio_buffer:
            self.audio_buffer[websocket] += audio_data

    def get_audio_buffer(self, websocket: WebSocket) -> bytes:
        """Get accumulated audio buffer for a specific client"""
        return self.audio_buffer.get(websocket, b"")

    def clear_audio_buffer(self, websocket: WebSocket):
        """Clear audio buffer for a specific client"""
        if websocket in self.audio_buffer:
            self.audio_buffer[websocket] = b""

# Audio processing functions
def convert_audio_to_wav(audio_data: bytes, sample_rate: int = 16000) -> bytes:
    """Convert raw audio data to WAV format for OpenAI Whisper"""
    try:
        # Convert numpy array to WAV format
        audio_array = np.frombuffer(audio_data, dtype=np.float32)
        
        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes((audio_array * 32767).astype(np.int16).tobytes())
        
        wav_buffer.seek(0)
        return wav_buffer.read()
    except Exception as e:
        logger.error(f"Error converting audio to WAV: {e}")
        return b""

async def transcribe_audio(audio_data: bytes) -> str:
    """Transcribe audio using OpenAI Whisper"""
    try:
        if not audio_data:
            return ""
        
        # Convert to WAV format
        wav_data = convert_audio_to_wav(audio_data)
        if not wav_data:
            return ""
        
        # Create a file-like object for OpenAI API
        audio_file = io.BytesIO(wav_data)
        audio_file.name = "audio.wav"
        
        # Transcribe using Whisper
        response = await asyncio.to_thread(
            openai.Audio.transcribe,
            model="whisper-1",
            file=audio_file,
            language="en"  # You can make this configurable
        )
        
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return ""

async def translate_text(text: str, target_language: str = "Spanish") -> str:
    """Translate text using OpenAI GPT"""
    try:
        if not text.strip():
            return ""
        
        prompt = f"Translate the following text to {target_language}. Only return the translation, no additional text:\n\n{text}"
        
        response = await asyncio.to_thread(
            openai.ChatCompletion.create,
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error translating text: {e}")
        return ""

app = FastAPI()
manager = ConnectionManager()

@app.get('/')
async def health_check():
    return {'status': 'Instant Translator service running', 'version': '1.0.0'}

@app.websocket("/audio")
async def audio_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    # Configuration
    BUFFER_DURATION = 3.0  # seconds
    SAMPLE_RATE = 16000
    CHUNK_SIZE = 1024
    BUFFER_SIZE = int(SAMPLE_RATE * BUFFER_DURATION * 4)  # 4 bytes per float32
    
    try:
        while True:
            audio_data = await websocket.receive_bytes()
            
            # Add audio chunk to buffer
            manager.add_audio_chunk(websocket, audio_data)
            
            # Check if buffer is ready for processing
            buffer = manager.get_audio_buffer(websocket)
            if len(buffer) >= BUFFER_SIZE:
                logger.info(f"Processing audio buffer of size: {len(buffer)} bytes")
                
                # Transcribe audio
                transcription = await transcribe_audio(buffer)
                
                if transcription:
                    logger.info(f"Transcribed: {transcription}")
                    
                    # Translate text
                    translation = await translate_text(transcription)
                    
                    if translation:
                        logger.info(f"Translated: {translation}")
                        
                        # Send result to client
                        result = {
                            "original": transcription,
                            "translation": translation,
                            "timestamp": asyncio.get_event_loop().time()
                        }
                        
                        await websocket.send_text(json.dumps(result))
                
                # Clear buffer for next processing cycle
                manager.clear_audio_buffer(websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        manager.disconnect(websocket)

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8010))
    uvicorn.run(app, host=host, port=port)