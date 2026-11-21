#!/bin/zsh
# Download the samples listed in data/media.json into media/, shrunk:
# images -> JPEG, longest side 640 px (sips); audio -> first 25 s as 96 kbit/s MP3 (ffmpeg).
# Files already in media/ are kept; FORCE=1 re-downloads everything. Needs macOS sips and ffmpeg.
set -u
cd "${0:A:h}/.."
mkdir -p media .cache/raw
python3 -c '
import json, re
for name, items in json.load(open("data/media.json")).items():
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    for i, (kind, url) in enumerate(items):
        print(kind, f"{slug}-{i}", url)
' | while read kind slug url; do
  out="media/$slug.$([[ $kind == img ]] && echo jpg || echo mp3)"
  [[ -s $out && -z ${FORCE:-} ]] && continue
  ext="${url##*.}"; ext="${ext%%\?*}"
  raw=".cache/raw/$slug.$ext"
  curl -sfL -A tiiny-models-catalog -o "$raw" "$url" || { echo "download failed: $slug $url"; continue; }
  if [[ $kind == img ]]; then
    sips -s format jpeg -s formatOptions 72 -Z 640 "$raw" --out "$out" >/dev/null || echo "convert failed: $slug"
  else
    ffmpeg -loglevel error -y -i "$raw" -t 25 -af "afade=t=out:st=23:d=2" -b:a 96k "$out" || echo "convert failed: $slug"
  fi
  echo "added $out"
done
