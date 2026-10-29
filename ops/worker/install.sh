#!/usr/bin/env bash
# Installs and starts the Keeplyn worker as user services (runs while you're logged in;
# run `sudo loginctl enable-linger "$USER"` once to keep it running after logout/reboot).
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
python3 "$here/keeplyn_worker.py" doctor
mkdir -p "$HOME/.config/systemd/user"
cp "$here"/systemd/keeplyn-worker-*.service "$HOME/.config/systemd/user/"
systemctl --user daemon-reload
systemctl --user enable --now keeplyn-worker-fast.service keeplyn-worker-build.service
systemctl --user --no-pager status keeplyn-worker-fast.service keeplyn-worker-build.service | grep -E 'Active|Loaded'
echo "Logs: journalctl --user -u keeplyn-worker-build -f   (or ~/.local/state/keeplyn-worker/worker.log)"
