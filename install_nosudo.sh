#!/usr/bin/env bash
# install_nosudo.sh — installe whisper-type sur une machine Debian/Ubuntu SANS
# droits sudo. Alternative à install.sh (qui suppose `sudo dnf`, Fedora + Hyprland).
#
# Astuce : `apt-get download <paquet>` ne demande pas sudo (il télécharge juste
# le .deb dans le dossier courant, sans l'installer). On extrait ensuite ces
# .deb avec `dpkg -x` (extraction pure, pas d'install système) dans .local/,
# et on pointe PATH/LD_LIBRARY_PATH dessus au lancement du daemon.
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL="$DIR/.local"
MULTIARCH="$(gcc -print-multiarch 2>/dev/null || echo x86_64-linux-gnu)"
LIBDIR="$LOCAL/usr/lib/$MULTIARCH"
BINDIR="$LOCAL/usr/bin"

echo "=== whisper-type installer (sans sudo) ==="

command -v apt-get >/dev/null || { echo "apt-get introuvable — ce script suppose une base Debian/Ubuntu."; exit 1; }

mkdir -p "$LOCAL"

# 1. Paquets système récupérés en .deb, extraits localement (aucune install système)
echo ""
echo "[1/5] Téléchargement + extraction des paquets système..."
PKGS=(libportaudio2)
if [ "$XDG_SESSION_TYPE" != "wayland" ]; then
    PKGS+=(xdotool libxdo3)
fi
command -v notify-send >/dev/null || PKGS+=(libnotify-bin)

DEBS_DIR="$(mktemp -d)"
(cd "$DEBS_DIR" && apt-get download "${PKGS[@]}")
for deb in "$DEBS_DIR"/*.deb; do
    dpkg -x "$deb" "$LOCAL"
done
rm -rf "$DEBS_DIR"

# ctypes.util.find_library('portaudio') (utilisé par sounddevice) cherche le
# lien non-versionné via une sonde gcc — le paquet runtime ne fournit que
# libportaudio.so.2, on ajoute le lien nous-mêmes.
if [ -e "$LIBDIR/libportaudio.so.2" ] && [ ! -e "$LIBDIR/libportaudio.so" ]; then
    ln -s libportaudio.so.2 "$LIBDIR/libportaudio.so"
fi

# 2. venv + dépendances Python
echo ""
echo "[2/5] Création de l'environnement Python..."
python3 -m venv "$DIR/.venv"
"$DIR/.venv/bin/pip" install --upgrade pip -q
"$DIR/.venv/bin/pip" install -r "$DIR/requirements.txt" -q

# 3. Variables d'environnement pour retrouver les libs/binaires extraits
echo ""
echo "[3/5] Écriture de .local/env.sh..."
cat > "$LOCAL/env.sh" <<EOF
# Généré par install_nosudo.sh — sourcé par start.sh, ne pas éditer à la main.
export PATH="$BINDIR:\$PATH"
export LD_LIBRARY_PATH="$LIBDIR:\$LD_LIBRARY_PATH"
export LIBRARY_PATH="$LIBDIR:\$LIBRARY_PATH"
EOF

# 4. Permissions
echo ""
echo "[4/5] Permissions..."
chmod +x "$DIR/whisper_type.py" "$DIR/toggle.sh" "$DIR/start.sh" "$DIR/stop.sh"

# 5. Raccourci clavier GNOME natif (F9) — pas de fichier de config global à
# éditer (contrairement au bind Hyprland d'install.sh), gsettings suffit.
echo ""
echo "[5/5] Raccourci clavier GNOME (F9)..."
if command -v gsettings >/dev/null 2>&1; then
    SCHEMA="org.gnome.settings-daemon.plugins.media-keys"
    CUSTOM_PATH="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/whispertype/"

    EXISTING="$(gsettings get $SCHEMA custom-keybindings)"
    if [[ "$EXISTING" != *"whispertype"* ]]; then
        if [ "$EXISTING" == "@as []" ]; then
            NEW="['$CUSTOM_PATH']"
        else
            NEW="${EXISTING%]}, '$CUSTOM_PATH']"
        fi
        gsettings set $SCHEMA custom-keybindings "$NEW"
    fi

    gsettings set "$SCHEMA.custom-keybinding:$CUSTOM_PATH" name "whisper-type toggle"
    gsettings set "$SCHEMA.custom-keybinding:$CUSTOM_PATH" command "$DIR/toggle.sh"
    gsettings set "$SCHEMA.custom-keybinding:$CUSTOM_PATH" binding "F9"
    echo "  F9 lié à $DIR/toggle.sh"
else
    echo "  gsettings non disponible (pas GNOME ?) — lie F9 manuellement à : $DIR/toggle.sh"
fi

echo ""
echo "=== Installation terminée ==="
echo ""
echo "Modèle : small (fr) — modifie ~/.config/whisper-type/config.toml pour changer"
echo ""
echo "Démarre maintenant avec :"
echo "  $DIR/start.sh"
echo "Puis F9 pour démarrer/arrêter l'enregistrement."
