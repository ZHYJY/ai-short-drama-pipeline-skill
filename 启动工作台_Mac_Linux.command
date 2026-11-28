#!/bin/sh
cd "$(dirname "$0")" || exit 1
python3 "asset-locked-storyboard-video/scripts/studio_server.py" --project "projects/我的短剧"
