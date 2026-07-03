#!/usr/bin/env python3
"""
whisper-type — enregistre le micro, transcrit avec Whisper, tape le texte dans l'input actif.

Config : ~/.config/whisper-type/config.toml
Signals : SIGUSR1 → toggle start/stop  |  SIGTERM/SIGINT → arrêt propre
"""

import os
import sys
import signal
import threading
import subprocess
import logging
import tempfile
from pathlib import Path

import config as cfg
import core

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

PID_FILE = Path(tempfile.gettempdir()) / "whisper-type.pid"
_config = cfg.load()
MODEL_SIZE = _config["model"]
LANGUAGE   = _config["language"]

recorder    = core.Recorder()
transcriber = core.Transcriber(MODEL_SIZE, LANGUAGE)


def notify(title, msg="", icon="dialog-information"):
    subprocess.run(["notify-send", "-i", icon, title, msg], check=False)


def load_model():
    notify("whisper-type", f"Chargement modèle {MODEL_SIZE}...", "audio-input-microphone")
    transcriber.load()
    notify("whisper-type", "Prêt — raccourci actif", "audio-input-microphone")


def start_recording():
    log.info("Enregistrement démarré...")
    notify("Enregistrement...", "Parle maintenant", "media-record")
    recorder.start()


def stop_and_transcribe():
    wav_path = recorder.stop()
    if wav_path is None:
        log.warning("Aucun audio enregistré.")
        return

    if not transcriber.is_loaded:
        notify("whisper-type", "Modèle en cours de chargement, réessayez dans quelques secondes", "dialog-warning")
        os.unlink(wav_path)
        return

    log.info("Transcription en cours...")
    notify("Transcription...", "", "hourglass")

    try:
        text = transcriber.transcribe(wav_path)
        log.info(f"Texte transcrit : {text!r}")
    finally:
        os.unlink(wav_path)

    if not text:
        notify("whisper-type", "Rien détecté", "dialog-warning")
        return

    type_text(text)
    notify("whisper-type", f"{text[:60]}{'...' if len(text) > 60 else ''}", "emblem-default")


def type_text(text):
    for cmd in [
        ["wtype", text],
        ["xdotool", "type", "--clearmodifiers", "--", text],
        ["ydotool", "type", "--", text],
    ]:
        if subprocess.run(["which", cmd[0]], capture_output=True).returncode == 0:
            result = subprocess.run(cmd, capture_output=True)
            if result.returncode == 0:
                log.info(f"Texte tapé avec {cmd[0]}")
                return
            log.warning(f"{cmd[0]} a échoué : {result.stderr.decode()}")

    log.warning("Aucun outil de typing disponible — copie dans le clipboard")
    subprocess.run(["wl-copy", text], input=text.encode(), check=False)
    notify("whisper-type", "Texte copié dans le clipboard (Ctrl+V)", "edit-paste")


def toggle_handler(signum, frame):
    if recorder.is_recording:
        threading.Thread(target=stop_and_transcribe, daemon=True).start()
    else:
        threading.Thread(target=start_recording, daemon=True).start()


def cleanup(signum=None, frame=None):
    recorder.abort()
    PID_FILE.unlink(missing_ok=True)
    log.info("Daemon arrêté.")
    sys.exit(0)


def main():
    PID_FILE.write_text(str(os.getpid()))
    log.info(f"Daemon démarré (PID {os.getpid()}, modèle={MODEL_SIZE}, langue={LANGUAGE})")

    threading.Thread(target=load_model, daemon=True).start()

    signal.signal(signal.SIGUSR1, toggle_handler)
    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)

    while True:
        signal.pause()


if __name__ == "__main__":
    main()
