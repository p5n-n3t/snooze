#!/usr/bin/env bash
set -euo pipefail
snooze_source="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python3 -c 'import sys; assert sys.version_info >= (3,11), "Python 3.11+ required"'
python3 -m venv "$snooze_source/.venv"
"$snooze_source/.venv/bin/python" -m pip install "$snooze_source"
mkdir -p "$HOME/.local/bin"
ln -sfn "$snooze_source/.venv/bin/snooze" "$HOME/.local/bin/snooze"
printf 'Installed: %s/.local/bin/snooze\n' "$HOME"
