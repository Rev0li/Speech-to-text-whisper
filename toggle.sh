#!/usr/bin/env bash
# toggle.sh — envoie SIGUSR1 au daemon pour démarrer/stopper l'enregistrement.
# Le bind Hyprland est ajouté par install.sh : bind = SUPER, F9, exec, <repo>/toggle.sh

PID_FILE="/tmp/whisper-type.pid"

if [ ! -f "$PID_FILE" ]; then
    notify-send -i "dialog-error" "whisper-type" "Daemon non démarré. Lance start.sh d'abord."
    exit 1
fi

PID=$(cat "$PID_FILE")

if ! kill -0 "$PID" 2>/dev/null; then
    notify-send -i "dialog-error" "whisper-type" "Daemon mort (PID $PID). Relance start.sh."
    rm -f "$PID_FILE"
    exit 1
fi

kill -USR1 "$PID"
