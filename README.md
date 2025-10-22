# Instant Translator

A real-time audio translation application that captures speech, transcribes it using OpenAI Whisper, and translates it using OpenAI GPT models. Perfect for live conversations, meetings, or any scenario where you need instant translation.

### Features
---

- **Real-time Audio Capture**: Continuous microphone input with WebSocket streaming
- **Speech-to-Text**: Powered by OpenAI Whisper for accurate transcription
- **AI Translation**: Uses OpenAI GPT models for high-quality translations
- **Live Display**: Real-time translation results with timestamps
- **Configurable**: Easy to customize languages, audio settings, and server configuration
- **Robust Error Handling**: Comprehensive logging and graceful error recovery

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- OpenAI API key
- Microphone access

### Installation

1. **Clone the repository**
    via `HTTP`
    ```bash
    git clone https://github.com/sulaiman-shamasna/instant-translator.git && cd instant-translator
    ```
    or via `SSH`:
    ```bash
    git clone git@github.com:sulaiman-shamasna/instant-translator.git && cd instant-translator
    ```
2. **Virtual environemnt**
   
   Create a virtual environemnt:
    ```bash
    python -m venv env
    ```
    and activate it (for two separate terminals - see later):
    ```bash
    source env/Scripts/activate   # for Git Bash on Windows
    source env/bin/activate       # for Linux/Mac
    ```


3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   Create a `.env` file, and add the `OPENAI_API_KEY` in it, it must look like:
   ```bash
   OPENAI_API_KEY="OPENAI_API_KEY"
   ```

5. **(Optional) Configure your .env file**
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   HOST=0.0.0.0
   PORT=8010
   SAMPLE_RATE=16000
   CHUNK_SIZE=1024
   ```

### Running the Application

1. **Start the translation server**
   ```bash
   python process_audio.py
   ```
   The server will start on `http://localhost:8010`

2. **Start the audio client** (in a new terminal)
   ```bash
   python stream_audio.py
   ```

3. **Start speaking!** The application will:
   - Capture your audio in real-time
   - Transcribe your speech using Whisper
   - Translate it using GPT
   - Display both original and translated text

### Configuration
---

#### Audio Settings
- `SAMPLE_RATE`: Audio sample rate (default: 16000 Hz)
- `CHUNK_SIZE`: Audio buffer size (default: 1024)

#### Server Settings
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8010)

#### Translation Settings
You can modify the translation language in `process_audio.py`:
```python
# Change target language in the translate_text function
translation = await translate_text(transcription, target_language="French")
```

## 📁 Project Structure

```
instant-translator/
├── process_audio.py      # FastAPI server with WebSocket endpoint
├── stream_audio.py      # Audio client for recording and display
├── requirements.txt      # Python dependencies
├── .env     # Environment variables 
└── README.md            # This file
```

**Happy Translating!**

**@TODOs**
- Speed up the inference
- Provide better APIs
- Containerize the application
- Add unittesting and automate CI/CD via GitHub Actions
- ...