#!/bin/bash
set -e
mv "$HOME/.config/user-dirs.dirs" "$HOME/.config/user-dirs.dirs.bak"
cat > "$HOME/.config/user-dirs.dirs" <<EOF
XDG_DESKTOP_DIR="\$HOME/Desktop"
XDG_DOWNLOAD_DIR="\$HOME/Downloads"
XDG_TEMPLATES_DIR="\$HOME"
XDG_PUBLICSHARE_DIR="\$HOME"
XDG_DOCUMENTS_DIR="\$HOME"
XDG_MUSIC_DIR="\$HOME"
XDG_PICTURES_DIR="\$HOME"
XDG_VIDEOS_DIR="\$HOME"
EOF
cat > "$HOME/.config/user-dirs.conf" <<EOF
enabled=false
EOF
