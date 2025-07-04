import asyncio
import websockets
import sounddevice as sd
import numpy as np

async def record_audio(websocket_url="ws://localhost:8000/audio"):
    """
    Records audio and sends it to a WebSocket server.
    
    Args:
        websocket_url: URL of the WebSocket server to connect to
    """
    audio_queue = asyncio.Queue()
    
    def audio_callback(indata: np.ndarray, frames: int, time: float, status: int) -> None:
        """Callback for sounddevice to process audio chunks."""
        if status:
            print(status, flush=True)
        audio_queue.put_nowait(indata.copy())
    
    try:
        async with websockets.connect(websocket_url) as ws:
            print("Connected to server\nAudio is being recorded...")
            
            with sd.InputStream(callback=audio_callback, blocksize=4200):
                while True:
                    audio = await audio_queue.get()
                    await ws.send(audio.tobytes())
                    
    except KeyboardInterrupt:
        print("Recording stopped by user")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(record_audio())