"""
Voice input processing for invoice creation.
Uses Whisper for speech-to-text.
"""

import io
import tempfile
from pathlib import Path
from typing import Optional
import httpx

from app.config import get_settings

settings = get_settings()


async def transcribe_audio(
    audio_bytes: bytes,
    filename: str = "audio.webm",
    language: Optional[str] = None
) -> str:
    """
    Transcribe audio to text using OpenAI Whisper API.
    
    Args:
        audio_bytes: Raw audio data
        filename: Original filename (for format detection)
        language: Optional language code (e.g., 'en', 'fr')
        
    Returns:
        Transcribed text
    """
    if not settings.openai_api_key:
        raise ValueError("OpenAI API key required for voice transcription")
    
    # Prepare the file for upload
    files = {
        'file': (filename, io.BytesIO(audio_bytes), 'audio/webm'),
        'model': (None, 'whisper-1'),
    }
    
    if language:
        files['language'] = (None, language)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            files=files,
            timeout=60.0
        )
        response.raise_for_status()
        data = response.json()
        return data.get("text", "")


async def transcribe_audio_local(
    audio_bytes: bytes,
    model_size: str = "base"
) -> str:
    """
    Transcribe audio using local Whisper model (if installed).
    
    Requires: pip install openai-whisper
    
    Args:
        audio_bytes: Raw audio data
        model_size: Whisper model size (tiny, base, small, medium, large)
        
    Returns:
        Transcribed text
    """
    try:
        import whisper
    except ImportError:
        raise ImportError("Local Whisper requires: pip install openai-whisper")
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
        f.write(audio_bytes)
        temp_path = f.name
    
    try:
        model = whisper.load_model(model_size)
        result = model.transcribe(temp_path)
        return result["text"]
    finally:
        Path(temp_path).unlink(missing_ok=True)


# Common voice commands for invoice creation
VOICE_EXAMPLES = [
    "Bill Johnson Electric for 3 hours troubleshooting, replaced a 30-amp breaker, and 45 minutes travel",
    "Invoice ABC Plumbing: 2 hours labor fixing the bathroom sink, plus a new faucet",
    "Charge Smith Construction for half day of framing work and materials",
    "Create invoice for Mary's Landscaping - 4 hours yard work, 2 bags of mulch",
]
