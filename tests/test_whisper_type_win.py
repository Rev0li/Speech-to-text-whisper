"""Tests unitaires pour whisper_type_win.py — TICKET-03.

keyboard / pyperclip / winotify ne sont pas installés dans le venv Linux de
dev (winotify est spécifique Windows). On les remplace par des doubles dans
sys.modules avant l'import du module, ce qui permet d'exercer réellement la
logique d'orchestration (contrairement à une simple vérification de syntaxe).
"""

import sys
from unittest.mock import Mock

import pytest


@pytest.fixture()
def wtw(monkeypatch):
    """Importe whisper_type_win avec ses dépendances Windows doublées."""
    fake_keyboard = Mock()
    fake_pyperclip = Mock()
    fake_notification_cls = Mock()
    fake_winotify = Mock(Notification=fake_notification_cls)

    monkeypatch.setitem(sys.modules, "keyboard", fake_keyboard)
    monkeypatch.setitem(sys.modules, "pyperclip", fake_pyperclip)
    monkeypatch.setitem(sys.modules, "winotify", fake_winotify)
    sys.modules.pop("whisper_type_win", None)

    import whisper_type_win as module

    monkeypatch.setattr(module.time, "sleep", lambda s: None)
    yield module

    sys.modules.pop("whisper_type_win", None)


class TestNotify:
    def test_shows_notification_with_app_id(self, wtw):
        wtw.notify("titre", "message")
        wtw.Notification.assert_called_once_with(app_id=wtw.APP_ID, title="titre", msg="message")
        wtw.Notification.return_value.show.assert_called_once()

    def test_swallows_exception_from_show(self, wtw):
        wtw.Notification.return_value.show.side_effect = Exception("pas de service toast")
        wtw.notify("titre", "message")  # ne doit pas lever


class TestTypeText:
    def test_pastes_via_ctrl_v_and_restores_clipboard(self, wtw):
        wtw.pyperclip.paste.return_value = "ancien contenu"

        wtw.type_text("bonjour")

        wtw.pyperclip.copy.assert_any_call("bonjour")
        wtw.keyboard.send.assert_called_once_with("ctrl+v")
        wtw.keyboard.write.assert_not_called()
        wtw.pyperclip.copy.assert_any_call("ancien contenu")
        assert wtw.pyperclip.copy.call_args_list[-1].args == ("ancien contenu",)

    def test_falls_back_to_keyboard_write_if_paste_fails(self, wtw):
        wtw.pyperclip.paste.return_value = ""
        wtw.keyboard.send.side_effect = Exception("collage impossible")

        wtw.type_text("bonjour")

        wtw.keyboard.write.assert_called_once_with("bonjour")

    def test_does_not_restore_clipboard_if_previous_read_failed(self, wtw):
        wtw.pyperclip.paste.side_effect = Exception("presse-papier verrouillé")

        wtw.type_text("bonjour")

        wtw.pyperclip.copy.assert_called_once_with("bonjour")  # jamais de 2e appel (restore)


class TestLoadModel:
    def test_notifies_ready_on_success(self, wtw, monkeypatch):
        wtw.transcriber = Mock()
        notify = Mock()
        monkeypatch.setattr(wtw, "notify", notify)

        wtw.load_model()

        wtw.transcriber.load.assert_called_once()
        messages = [c.args[1] if len(c.args) > 1 else "" for c in notify.call_args_list]
        assert any("charg" in m.lower() for m in messages)
        assert any("prêt" in m.lower() or "pret" in m.lower() for m in messages)

    def test_notifies_failure_without_crashing(self, wtw, monkeypatch):
        wtw.transcriber = Mock()
        wtw.transcriber.load.side_effect = RuntimeError("pas de réseau")
        notify = Mock()
        monkeypatch.setattr(wtw, "notify", notify)

        wtw.load_model()  # ne doit pas lever

        messages = [c.args[1] if len(c.args) > 1 else "" for c in notify.call_args_list]
        assert any("échec" in m.lower() for m in messages)


class TestToggle:
    def test_starts_recording_when_idle(self, wtw, monkeypatch):
        wtw.recorder = Mock(is_recording=False)
        started = Mock()
        monkeypatch.setattr(wtw, "start_recording", started)
        monkeypatch.setattr(wtw.threading, "Thread", _SyncThread)

        wtw.toggle()

        started.assert_called_once()

    def test_stops_and_transcribes_when_recording(self, wtw, monkeypatch):
        wtw.recorder = Mock(is_recording=True)
        stopped = Mock()
        monkeypatch.setattr(wtw, "stop_and_transcribe", stopped)
        monkeypatch.setattr(wtw.threading, "Thread", _SyncThread)

        wtw.toggle()

        stopped.assert_called_once()


class _SyncThread:
    """Remplace threading.Thread pour exécuter la cible de façon synchrone en test."""

    def __init__(self, target, daemon=True):
        self._target = target

    def start(self):
        self._target()


class TestStopAndTranscribe:
    def test_no_audio_recorded_is_a_noop(self, wtw, monkeypatch):
        wtw.recorder = Mock()
        wtw.recorder.stop.return_value = None
        unlink = Mock()
        monkeypatch.setattr(wtw.os, "unlink", unlink)

        wtw.stop_and_transcribe()

        unlink.assert_not_called()

    def test_notifies_and_cleans_up_when_model_not_loaded(self, wtw, monkeypatch):
        wtw.recorder = Mock()
        wtw.recorder.stop.return_value = "/tmp/fake.wav"
        wtw.transcriber = Mock(is_loaded=False)
        unlink = Mock()
        monkeypatch.setattr(wtw.os, "unlink", unlink)
        notify = Mock()
        monkeypatch.setattr(wtw, "notify", notify)

        wtw.stop_and_transcribe()

        unlink.assert_called_once_with("/tmp/fake.wav")
        wtw.transcriber.transcribe.assert_not_called()
        assert "charg" in notify.call_args.args[1].lower()

    def test_types_text_on_successful_transcription(self, wtw, monkeypatch):
        wtw.recorder = Mock()
        wtw.recorder.stop.return_value = "/tmp/fake.wav"
        wtw.transcriber = Mock(is_loaded=True)
        wtw.transcriber.transcribe.return_value = "bonjour le monde"
        monkeypatch.setattr(wtw.os, "unlink", Mock())
        type_text = Mock()
        monkeypatch.setattr(wtw, "type_text", type_text)

        wtw.stop_and_transcribe()

        type_text.assert_called_once_with("bonjour le monde")

    def test_does_not_type_when_transcription_is_empty(self, wtw, monkeypatch):
        wtw.recorder = Mock()
        wtw.recorder.stop.return_value = "/tmp/fake.wav"
        wtw.transcriber = Mock(is_loaded=True)
        wtw.transcriber.transcribe.return_value = ""
        monkeypatch.setattr(wtw.os, "unlink", Mock())
        type_text = Mock()
        monkeypatch.setattr(wtw, "type_text", type_text)

        wtw.stop_and_transcribe()

        type_text.assert_not_called()

    def test_unlinks_wav_even_if_transcription_raises(self, wtw, monkeypatch):
        wtw.recorder = Mock()
        wtw.recorder.stop.return_value = "/tmp/fake.wav"
        wtw.transcriber = Mock(is_loaded=True)
        wtw.transcriber.transcribe.side_effect = RuntimeError("modèle corrompu")
        unlink = Mock()
        monkeypatch.setattr(wtw.os, "unlink", unlink)

        with pytest.raises(RuntimeError):
            wtw.stop_and_transcribe()

        unlink.assert_called_once_with("/tmp/fake.wav")
