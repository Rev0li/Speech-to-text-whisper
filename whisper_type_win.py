#!/usr/bin/env python3
"""
whisper_type_win.py — entrée Windows : hotkey global, transcription, collage presse-papier.

Config : ~/.config/whisper-type/config.toml (clé `hotkey`, ignorée côté Linux)
Lancement recommandé : pythonw whisper_type_win.py (pas de fenêtre console)
Sortie propre : Ctrl+Alt+Q
"""

import logging
import os
import threading
import time

import keyboard
import pyperclip
from winotify import Notification

import config as cfg
import core

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

APP_ID = "whisper-type"

_config = cfg.load()
MODEL_SIZE = _config["model"]
LANGUAGE   = _config["language"]
HOTKEY     = _config["hotkey"]

recorder    = core.Recorder()
transcriber = core.Transcriber(MODEL_SIZE, LANGUAGE)


def notify(title, msg=""):
    try:
        Notification(app_id=APP_ID, title=title, msg=msg).show()
    except Exception as e:
        log.warning(f"Notification échouée : {e}")


def load_model():
    notify("whisper-type", f"Chargement modèle {MODEL_SIZE}...")
    try:
        transcriber.load()
    except Exception as e:
        log.error(f"Échec du chargement du modèle : {e}")
        notify("whisper-type", "Échec du chargement du modèle — voir les logs")
        return
    notify("whisper-type", "Prêt — raccourci actif")


def start_recording():
    log.info("Enregistrement démarré...")
    notify("Enregistrement...", "Parle maintenant")
    recorder.start()


def stop_and_transcribe():
    wav_path = recorder.stop()
    if wav_path is None:
        log.warning("Aucun audio enregistré.")
        return

    if not transcriber.is_loaded:
        notify("whisper-type", "Modèle en cours de chargement, réessayez dans quelques secondes")
        os.unlink(wav_path)
        return

    log.info("Transcription en cours...")
    notify("Transcription...", "")

    try:
        text = transcriber.transcribe(wav_path)
        log.info(f"Texte transcrit : {text!r}")
    finally:
        os.unlink(wav_path)

    if not text:
        notify("whisper-type", "Rien détecté")
        return

    type_text(text)
    notify("whisper-type", f"{text[:60]}{'...' if len(text) > 60 else ''}")


def type_text(text):
    """Colle `text` via le presse-papier (Ctrl+V) — fiable pour les accents/unicode.
    Sauvegarde puis restaure le presse-papier précédent. Fallback : frappe touche par touche.
    """
    previous_clipboard = None
    try:
        previous_clipboard = pyperclip.paste()
    except Exception as e:
        log.warning(f"Lecture presse-papier échouée : {e}")

    try:
        pyperclip.copy(text)
        keyboard.send("ctrl+v")
        log.info("Texte collé via Ctrl+V")
    except Exception as e:
        log.warning(f"Collage échoué ({e}) — fallback frappe touche par touche")
        keyboard.write(text)
    finally:
        if previous_clipboard is not None:
            time.sleep(0.3)
            try:
                pyperclip.copy(previous_clipboard)
            except Exception as e:
                log.warning(f"Restauration presse-papier échouée : {e}")


def toggle():
    if recorder.is_recording:
        threading.Thread(target=stop_and_transcribe, daemon=True).start()
    else:
        threading.Thread(target=start_recording, daemon=True).start()


def main():
    log.info(f"Daemon Windows démarré (modèle={MODEL_SIZE}, langue={LANGUAGE}, hotkey={HOTKEY})")

    threading.Thread(target=load_model, daemon=True).start()

    keyboard.add_hotkey(HOTKEY, toggle, suppress=True)
    log.info(f"Raccourci actif : {HOTKEY}  |  Ctrl+Alt+Q pour quitter.")

    keyboard.wait("ctrl+alt+q")

    log.info("Arrêt demandé (Ctrl+Alt+Q).")
    recorder.abort()
    keyboard.unhook_all()
    log.info("Daemon arrêté.")


if __name__ == "__main__":
    main()
