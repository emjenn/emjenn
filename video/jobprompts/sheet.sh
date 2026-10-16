#!/bin/sh
# usage: sheet.sh TAG  -> build/sheet_TAG.png (contact sheet of stills)
cd "$(dirname "$0")/build"
ffmpeg -hide_banner -loglevel error -y -pattern_type glob -i "$1_*.png" -vf "scale=640:360,tile=3x4:padding=4:color=gray" -frames:v 1 sheet_$1.png
