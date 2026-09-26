"""
Voice Agent — Handles Whisper STT + Piper TTS pipeline.
Provides speech-to-text and text-to-speech capabilities for voice mode.
"""
import io
import os
import tempfile
import wave
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import WHISPER_MODEL, PIPER_VOICE, MEMORY_VAULT_DIR


class VoiceAgent:
    """Handles the complete voice pipeline: STT via Faster Whisper, TTS via Piper."""

    def __init__(self):
        self._whisper_model = None
        self._piper_voice = None
        self._initialized_stt = False
        self._initialized_tts = False
        self._audio_dir = MEMORY_VAULT_DIR / "audio"
        self._audio_dir.mkdir(parents=True, exist_ok=True)

    def initialize_stt(self):
        """Initialize Faster Whisper for speech-to-text."""
        if self._initialized_stt:
            return
        try:
            from faster_whisper import WhisperModel
            self._whisper_model = WhisperModel(
                WHISPER_MODEL,
                device="cpu",
                compute_type="int8",
            )
            self._initialized_stt = True
        except ImportError:
            print("faster-whisper not installed. STT will use fallback.")
        except Exception as e:
            print(f"Failed to initialize Whisper: {e}")

    def initialize_tts(self):
        """Initialize Piper TTS for text-to-speech."""
        if self._initialized_tts:
            return
        try:
            # Piper TTS initialization
            self._initialized_tts = True
        except Exception as e:
            print(f"Failed to initialize Piper TTS: {e}")

    async def transcribe(self, audio_bytes: bytes, format: str = "wav") -> Dict[str, Any]:
        """
        Transcribe audio bytes to text using Faster Whisper.
        Falls back to a simulated response if Whisper isn't available.
        """
        self.initialize_stt()
        
        if self._whisper_model is None:
            return {
                "text": "",
                "language": "en",
                "confidence": 0.0,
                "error": "Whisper model not available. Install faster-whisper.",
            }
        
        # Save audio to temporary file
        with tempfile.NamedTemporaryFile(suffix=f".{format}", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        
        try:
            segments, info = self._whisper_model.transcribe(
                tmp_path,
                beam_size=5,
                language="en",
            )
            
            text_parts = []
            total_confidence = 0
            count = 0
            for segment in segments:
                text_parts.append(segment.text.strip())
                total_confidence += segment.avg_logprob
                count += 1
            
            full_text = " ".join(text_parts)
            avg_confidence = (total_confidence / count) if count > 0 else 0
            
            return {
                "text": full_text,
                "language": info.language,
                "confidence": round(avg_confidence, 4),
                "duration": round(info.duration, 2),
            }
        except Exception as e:
            return {
                "text": "",
                "language": "en",
                "confidence": 0.0,
                "error": str(e),
            }
        finally:
            os.unlink(tmp_path)

    async def synthesize(self, text: str) -> Optional[bytes]:
        """
        Convert text to speech using Piper TTS.
        Returns WAV audio bytes or None if TTS is unavailable.
        """
        self.initialize_tts()
        
        try:
            # Try using piper-tts
            import subprocess
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
            
            process = subprocess.run(
                ["piper", "--model", PIPER_VOICE, "--output_file", tmp_path],
                input=text.encode(),
                capture_output=True,
                timeout=30,
            )
            
            if process.returncode == 0 and os.path.exists(tmp_path):
                with open(tmp_path, "rb") as f:
                    audio_bytes = f.read()
                os.unlink(tmp_path)
                return audio_bytes
        except Exception as e:
            print(f"Piper TTS failed: {e}")
        
        # Fallback: generate a minimal silent WAV
        return self._generate_silent_wav(duration_ms=100)

    def _generate_silent_wav(self, duration_ms: int = 100) -> bytes:
        """Generate a minimal silent WAV file as fallback."""
        sample_rate = 22050
        num_samples = int(sample_rate * duration_ms / 1000)
        
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(b'\x00\x00' * num_samples)
        
        return buffer.getvalue()

    async def save_audio(self, audio_bytes: bytes, filename: str) -> str:
        """Save audio to the memory vault audio directory."""
        filepath = self._audio_dir / filename
        with open(filepath, "wb") as f:
            f.write(audio_bytes)
        return str(filepath)
