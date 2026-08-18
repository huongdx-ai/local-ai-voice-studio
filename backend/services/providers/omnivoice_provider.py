"""
OmniVoice TTS Provider for Local AI Voice Studio.
Uses k2-fsa/OmniVoice (v0.2.1) for high-quality multilingual TTS, zero-shot voice cloning,
and natural language voice design.
"""

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Optional, Union

import numpy as np

from backend.services.tts_provider import TTSProvider, TTSRequest, TTSResult, ProviderCapabilities

logger = logging.getLogger(__name__)


class OmniVoiceProvider(TTSProvider):
    """
    OmniVoice TTS provider using k2-fsa/OmniVoice 0.2.1.
    
    Full features:
    - 600+ languages (EN, VI, JA, ZH, KO, FR, DE, ES, etc.)
    - Zero-shot voice cloning via reference audio (.wav) or pre-extracted VoiceClonePrompt (.pt)
    - Voice design with sanitized OmniVoice keywords (female, male, low pitch, whisper, etc.)
    - Expressive non-verbal tags ([laughter], [sigh], [gasp], [whisper], etc.)
    - Diffusion configuration: num_step, guidance_scale, denoise
    - Duration and speed control
    - ASR transcription for reference audio
    - Automatic hardware acceleration (CUDA/CPU with FP16/FP32)
    """

    VALID_EN_INSTRUCTS = {
        'american accent', 'australian accent', 'british accent', 'canadian accent',
        'child', 'chinese accent', 'elderly', 'female', 'high pitch', 'indian accent',
        'japanese accent', 'korean accent', 'low pitch', 'male', 'middle-aged',
        'moderate pitch', 'portuguese accent', 'russian accent', 'teenager',
        'very high pitch', 'very low pitch', 'whisper', 'young adult'
    }

    def __init__(self):
        self._model = None
        self._loaded = False
        self._device = "cpu"
        self._sample_rate = 24000  # OmniVoice native sample rate: 24kHz

    def get_engine_id(self) -> str:
        return "omnivoice"

    def get_name(self) -> str:
        return "OmniVoice"

    def get_display_name(self) -> str:
        return "OmniVoice 0.2.1 (k2-fsa)"

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            languages=[
                "en", "vi", "ja", "zh", "ko", "fr", "de", "es", "it", "pt",
                "ru", "ar", "hi", "th", "id", "ms", "tl", "tr", "pl", "nl",
            ],
            voice_cloning=True,
            voice_design=True,
            speed_control=True,
            pitch_control=False,
            streaming=False,
            max_text_length=5000,
            supported_sample_rates=[24000],
        )

    def supports_language(self, language: str) -> bool:
        """OmniVoice supports 600+ languages natively."""
        return True

    def supports_cloning(self) -> bool:
        return True

    def is_loaded(self) -> bool:
        return self._loaded

    async def initialize(self, device: str = "cpu") -> None:
        """Initialize and load the OmniVoice model."""
        self._device = device
        logger.info(f"Initializing OmniVoice on device: {device}")

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._load_model)
            self._loaded = True
            logger.info("OmniVoice model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OmniVoice: {e}")
            raise RuntimeError(f"Failed to load OmniVoice model: {e}")

    def _load_model(self) -> None:
        """Load the OmniVoice model from pretrained weights in thread pool."""
        import torch
        from omnivoice import OmniVoice

        device = self._device
        if device == "cuda" and not torch.cuda.is_available():
            device = "cpu"
            self._device = "cpu"

        torch_dtype = torch.float16 if device == "cuda" else torch.float32

        logger.info(f"Loading OmniVoice from k2-fsa/OmniVoice on {device} ({torch_dtype})...")
        self._model = OmniVoice.from_pretrained(
            "k2-fsa/OmniVoice",
            torch_dtype=torch_dtype,
        )
        self._model.to(device)
        self._model.eval()

    def _map_language(self, lang_code: str) -> str:
        """Map ISO language code or friendly name to OmniVoice language name."""
        mapping = {
            "en": "english",
            "english": "english",
            "vi": "vietnamese",
            "vietnamese": "vietnamese",
            "ja": "japanese",
            "japanese": "japanese",
            "zh": "mandarin chinese",
            "chinese": "mandarin chinese",
            "ko": "korean",
            "korean": "korean",
            "fr": "french",
            "french": "french",
            "de": "german",
            "german": "german",
            "es": "spanish",
            "spanish": "spanish",
            "it": "italian",
            "italian": "italian",
            "pt": "portuguese",
            "portuguese": "portuguese",
            "ru": "russian",
            "russian": "russian",
            "ar": "standard arabic",
            "arabic": "standard arabic",
            "hi": "hindi",
            "hindi": "hindi",
            "th": "thai",
            "thai": "thai",
            "id": "indonesian",
            "indonesian": "indonesian",
            "ms": "malay",
            "malay": "malay",
        }
        clean = lang_code.strip().lower()
        return mapping.get(clean, clean)

    def _sanitize_instruct(self, raw_instruct: Optional[str]) -> Optional[str]:
        """
        Sanitizes instruct input to ensure only valid OmniVoice items are passed.
        Prevents runtime exceptions from invalid keywords.
        """
        if not raw_instruct or not raw_instruct.strip():
            return None

        text = raw_instruct.lower().strip().replace('，', ',')
        valid_tokens = []

        # 1. Check direct comma-separated tokens
        parts = [p.strip() for p in text.split(',')]
        for p in parts:
            if p in self.VALID_EN_INSTRUCTS:
                if p not in valid_tokens:
                    valid_tokens.append(p)

        # 2. Heuristic extraction if no direct matches
        if not valid_tokens:
            if any(w in text for w in ['female', 'nữ', 'woman', 'girl', 'cô', 'chị', 'bà']):
                valid_tokens.append('female')
            elif any(w in text for w in ['male', 'nam', 'man', 'boy', 'anh', 'ông', 'chú']):
                valid_tokens.append('male')

            if any(w in text for w in ['whisper', 'thì thầm', 'soothing']):
                valid_tokens.append('whisper')
            elif any(w in text for w in ['very low', 'rất trầm', 'cinematic']):
                valid_tokens.append('very low pitch')
            elif any(w in text for w in ['deep', 'trầm', 'low pitch', 'low']):
                valid_tokens.append('low pitch')
            elif any(w in text for w in ['cute', 'cao', 'high pitch', 'bright']):
                valid_tokens.append('high pitch')
            elif any(w in text for w in ['moderate', 'vừa phải']):
                valid_tokens.append('moderate pitch')

            if any(w in text for w in ['elderly', 'old', 'lớn tuổi', 'già', 'grandfather']):
                valid_tokens.append('elderly')
            elif any(w in text for w in ['middle', 'trung niên']):
                valid_tokens.append('middle-aged')
            elif any(w in text for w in ['teen', 'thiếu niên']):
                valid_tokens.append('teenager')
            elif any(w in text for w in ['young', 'trẻ']):
                valid_tokens.append('young adult')

        # Clean mutually exclusive tokens
        if 'male' in valid_tokens and 'female' in valid_tokens:
            valid_tokens.remove('male')

        if valid_tokens:
            sanitized = ', '.join(valid_tokens)
            logger.info(f"Sanitized instruct: '{raw_instruct}' -> '{sanitized}'")
            return sanitized

        logger.info(f"Instruct '{raw_instruct}' contains no valid keywords; omitting to avoid error.")
        return None

    def extract_voice_clone_prompt(
        self,
        ref_audio_path: Union[str, Path],
        ref_text: Optional[str] = None,
    ):
        """Extract VoiceClonePrompt from audio sample for reusable caching."""
        if not self._loaded or self._model is None:
            raise RuntimeError("Model not loaded")

        ref_audio_str = str(ref_audio_path)
        logger.info(f"Extracting voice clone prompt from: {ref_audio_str}")
        return self._model.create_voice_clone_prompt(
            ref_audio=ref_audio_str,
            ref_text=ref_text,
            preprocess_prompt=True,
        )

    def transcribe_audio(self, audio_path: Union[str, Path]) -> str:
        """Transcribe an audio file using OmniVoice ASR."""
        if not self._loaded or self._model is None:
            raise RuntimeError("Model not loaded")
        try:
            return self._model.transcribe(str(audio_path))
        except Exception as e:
            logger.warning(f"Audio transcription failed: {e}")
            return ""

    async def generate(self, request: TTSRequest) -> TTSResult:
        """Generate speech using OmniVoice with full 0.2.1 capabilities."""
        if not self._loaded or self._model is None:
            return TTSResult(
                audio_path=Path(""),
                success=False,
                error="OmniVoice model not loaded. Call initialize() first.",
            )

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._generate_sync,
                request,
            )
            return result
        except Exception as e:
            logger.error(f"OmniVoice generation error: {e}")
            return TTSResult(
                audio_path=Path(""),
                success=False,
                error=str(e),
            )

    def _generate_sync(self, request: TTSRequest) -> TTSResult:
        """Synchronous generation execution in thread pool."""
        import soundfile as sf
        import time
        from omnivoice import OmniVoiceGenerationConfig, VoiceClonePrompt

        start_time = time.time()
        lang_name = self._map_language(request.language)

        # 1. Base generation kwargs
        kwargs = {
            "text": request.text,
            "language": lang_name,
        }

        # 2. Voice Design (Sanitized instruct parameter)
        sanitized_instruct = self._sanitize_instruct(request.instruct)
        if sanitized_instruct:
            kwargs["instruct"] = sanitized_instruct

        # 3. Voice Cloning: Pre-extracted VoiceClonePrompt (.pt) or Audio (.wav)
        prompt_loaded = False
        if request.voice_prompt_path:
            p_path = Path(request.voice_prompt_path)
            if p_path.exists():
                try:
                    kwargs["voice_clone_prompt"] = VoiceClonePrompt.load(str(p_path))
                    prompt_loaded = True
                    logger.info(f"Loaded cached VoiceClonePrompt: {p_path.name}")
                except Exception as e:
                    logger.warning(f"Failed to load cached prompt {p_path}: {e}")

        if not prompt_loaded and request.voice_profile_path:
            ref_path = Path(request.voice_profile_path)
            if ref_path.exists():
                kwargs["ref_audio"] = str(ref_path)
                if request.ref_text:
                    kwargs["ref_text"] = request.ref_text
                logger.info(f"Using reference audio for cloning: {ref_path.name}")

        # 4. Speed & Duration control
        if request.speed and request.speed != 1.0:
            kwargs["speed"] = float(request.speed)

        if request.duration and request.duration > 0:
            kwargs["duration"] = float(request.duration)

        # 5. Advanced Diffusion Generation Config
        gen_config = OmniVoiceGenerationConfig(
            num_step=request.num_step if hasattr(request, "num_step") and request.num_step else 32,
            guidance_scale=request.guidance_scale if hasattr(request, "guidance_scale") and request.guidance_scale else 2.0,
            denoise=request.denoise if hasattr(request, "denoise") else True,
            preprocess_prompt=True,
            postprocess_output=True,
        )
        kwargs["generation_config"] = gen_config

        logger.info(
            f"OmniVoice generate: lang={lang_name}, text_len={len(request.text)}, "
            f"cloning={'prompt' if prompt_loaded else ('audio' if 'ref_audio' in kwargs else 'none')}, "
            f"instruct={kwargs.get('instruct')}"
        )

        # Execute generation
        raw_output = self._model.generate(**kwargs)

        if isinstance(raw_output, list) and len(raw_output) > 0:
            audio = raw_output[0]
        else:
            audio = raw_output

        if audio is None or len(audio) == 0:
            return TTSResult(
                audio_path=Path(""),
                success=False,
                error="OmniVoice returned empty audio output",
            )

        if not isinstance(audio, np.ndarray):
            audio = np.array(audio, dtype=np.float32)

        # Normalize audio headroom
        max_val = np.max(np.abs(audio))
        if max_val > 0.99:
            audio = audio / max_val * 0.95

        # Save generated audio to WAV
        output_path = Path(tempfile.mktemp(suffix=".wav"))
        sf.write(str(output_path), audio, self._sample_rate)

        elapsed = time.time() - start_time
        duration = len(audio) / self._sample_rate

        logger.info(
            f"OmniVoice generation complete: duration={duration:.2f}s, "
            f"elapsed={elapsed:.2f}s, RTF={elapsed/duration:.3f}"
        )

        return TTSResult(
            audio_path=output_path,
            success=True,
            duration_seconds=round(duration, 2),
            model_used="OmniVoice 0.2.1",
            language=request.language,
            sample_rate=self._sample_rate,
        )

    async def unload(self) -> None:
        """Unload model to free GPU VRAM / RAM."""
        if self._model is not None:
            del self._model
            self._model = None
            self._loaded = False

            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass

            logger.info("OmniVoice model unloaded from memory")
