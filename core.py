"""core.py — cœur portable : enregistrement micro + transcription Whisper.

Aucune dépendance spécifique à une plateforme (pas de `signal`, pas de
`subprocess` vers des outils Linux). Réutilisable tel quel par une future
entrée Windows (voir TICKET-03).
"""

import logging
import tempfile
import threading
import wave

log = logging.getLogger(__name__)


def _resolve_language(language):
    """Convertit la valeur de config en argument attendu par faster-whisper."""
    return None if language == "auto" else language


class Recorder:
    """Capture micro (16 kHz mono int16) vers un fichier WAV temporaire."""

    def __init__(self, samplerate=16000, channels=1):
        self.samplerate = samplerate
        self.channels = channels
        self._recording = False
        self._frames = []
        self._lock = threading.Lock()
        self._stream = None

    @property
    def is_recording(self):
        return self._recording

    def start(self):
        import sounddevice as sd

        with self._lock:
            if self._recording:
                return
            self._recording = True
            self._frames = []

        def callback(indata, frames, time_info, status):
            if self._recording:
                self._frames.append(indata.copy())

        try:
            self._stream = sd.InputStream(
                samplerate=self.samplerate,
                channels=self.channels,
                dtype="int16",
                callback=callback,
            )
            self._stream.start()
        except Exception as e:
            log.error(f"Microphone inaccessible : {e}")
            with self._lock:
                self._recording = False

    def stop(self):
        """Arrête l'enregistrement et écrit un WAV temporaire.

        Retourne le chemin du WAV, ou None si rien n'était en cours /
        aucune frame n'a été capturée.
        """
        import numpy as np

        with self._lock:
            if not self._recording:
                return None
            self._recording = False

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        if not self._frames:
            return None

        audio = np.concatenate(self._frames, axis=0).flatten()

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wav_path = f.name

        with wave.open(wav_path, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)
            wf.setframerate(self.samplerate)
            wf.writeframes(audio.tobytes())

        return wav_path

    def abort(self):
        """Arrête l'enregistrement sans écrire de WAV (fermeture du daemon)."""
        with self._lock:
            self._recording = False

        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None


class Transcriber:
    """Charge un modèle faster-whisper (lazy) et transcrit des WAV en texte."""

    def __init__(self, model_size, language="auto"):
        self.model_size = model_size
        self.language = language
        self._model = None

    @property
    def is_loaded(self):
        return self._model is not None

    def load(self):
        if self._model is not None:
            return
        from faster_whisper import WhisperModel

        log.info(f"Chargement du modèle Whisper '{self.model_size}'...")
        self._model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
        log.info("Modèle chargé.")

    def transcribe(self, wav_path) -> str:
        """Transcrit un fichier WAV. Charge le modèle si besoin (lazy)."""
        if self._model is None:
            self.load()

        segments, _ = self._model.transcribe(
            wav_path,
            language=_resolve_language(self.language),
            beam_size=5,
            vad_filter=True,
        )
        return " ".join(s.text.strip() for s in segments).strip()
