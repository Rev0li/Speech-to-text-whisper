"""Tests unitaires pour core.py — TICKET-02."""

import os
import wave
from unittest.mock import Mock

import numpy as np
import pytest

import core


class TestResolveLanguage:
    def test_auto_converts_to_none(self):
        assert core._resolve_language("auto") is None

    def test_fr_left_unchanged(self):
        assert core._resolve_language("fr") == "fr"

    def test_en_left_unchanged(self):
        assert core._resolve_language("en") == "en"


class TestRecorderStop:
    def test_stop_without_active_recording_returns_none(self):
        rec = core.Recorder()
        assert rec.stop() is None

    def test_stop_with_no_frames_returns_none(self):
        rec = core.Recorder()
        rec._recording = True
        rec._frames = []
        assert rec.stop() is None

    def test_stop_writes_wav_from_fake_frames(self):
        rec = core.Recorder(samplerate=16000, channels=1)
        rec._recording = True
        rec._frames = [
            np.zeros((100, 1), dtype="int16"),
            np.ones((50, 1), dtype="int16"),
        ]

        wav_path = rec.stop()
        try:
            assert wav_path is not None
            assert os.path.exists(wav_path)
            with wave.open(wav_path, "rb") as wf:
                assert wf.getnchannels() == 1
                assert wf.getsampwidth() == 2
                assert wf.getframerate() == 16000
                assert wf.getnframes() == 150
        finally:
            os.unlink(wav_path)

    def test_stop_resets_recording_state(self):
        rec = core.Recorder()
        rec._recording = True
        rec._frames = [np.zeros((10, 1), dtype="int16")]
        wav_path = rec.stop()
        try:
            assert rec.is_recording is False
        finally:
            if wav_path:
                os.unlink(wav_path)


class TestRecorderAbort:
    def test_abort_resets_recording_without_writing_wav(self):
        rec = core.Recorder()
        rec._recording = True
        rec._frames = [np.zeros((10, 1), dtype="int16")]
        rec.abort()
        assert rec.is_recording is False

    def test_abort_when_not_recording_is_a_noop(self):
        rec = core.Recorder()
        rec.abort()
        assert rec.is_recording is False


class TestTranscriber:
    def test_not_loaded_by_default(self):
        t = core.Transcriber(model_size="tiny", language="fr")
        assert t.is_loaded is False

    def test_transcribe_uses_resolved_language_and_joins_segments(self):
        t = core.Transcriber(model_size="tiny", language="auto")
        fake_model = Mock()
        fake_model.transcribe.return_value = (
            [Mock(text=" bonjour "), Mock(text="le monde ")],
            None,
        )
        t._model = fake_model

        result = t.transcribe("fake.wav")

        assert result == "bonjour le monde"
        fake_model.transcribe.assert_called_once_with(
            "fake.wav", language=None, beam_size=5, vad_filter=True
        )

    def test_transcribe_passes_through_explicit_language(self):
        t = core.Transcriber(model_size="tiny", language="fr")
        fake_model = Mock()
        fake_model.transcribe.return_value = ([], None)
        t._model = fake_model

        t.transcribe("fake.wav")

        fake_model.transcribe.assert_called_once_with(
            "fake.wav", language="fr", beam_size=5, vad_filter=True
        )

    def test_transcribe_loads_model_lazily_if_not_loaded(self):
        t = core.Transcriber(model_size="tiny", language="fr")
        loaded = Mock()
        loaded.transcribe.return_value = ([], None)

        def fake_load():
            t._model = loaded

        t.load = fake_load
        t.transcribe("fake.wav")

        assert t._model is loaded
        loaded.transcribe.assert_called_once()
