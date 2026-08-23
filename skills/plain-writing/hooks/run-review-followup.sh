#!/bin/sh
# Run the writing-pass review hook from the plugin or the repo.
set -e
HERE="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"
exec python3 "$HERE/review_followup.py" "$@"
