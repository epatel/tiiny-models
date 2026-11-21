# samples

How sample images and audio get from a maker's page into `media/` (`make media` → `scripts/media.sh`).

**Input.** `data/media.json`: `name: [["img"|"aud", url], ...]`. URLs come from `make digest` (it prints image/audio links found in the cached model card, generating types only) or from the maker's demo page / GitHub. Only the makers' own published examples, never ones we generate.

**Steps per item:**
1. Output path `media/<slug>-<i>.jpg` (img) or `.mp3` (aud), `<i>` = position in the list.
2. Skipped if that file exists and is non-empty, unless `FORCE=1`.
3. Download with curl to `.cache/raw/<slug>-<i>.<ext>` (user agent `tiiny-models-catalog`).
4. Images: `sips` → JPEG quality 72, longest side 640 px. Audio: `ffmpeg` → first 25 s, 2 s fade-out from 23 s, 96 kbit/s MP3.
5. Prints `added …`, or `download failed: …` / `convert failed: …` and moves on (the script does not stop on errors).

**Requirements.** zsh, macOS `sips`, `ffmpeg` (`brew install ffmpeg`). Not portable to Linux as written.

**Failure modes:**
- *Gated Hugging Face repos* (e.g. krea/Krea-2-Turbo) return 401/403, so the download fails. Access must be requested by the user; never fill in access forms or accept licences.
- *Relative links in cards* are resolved by `card_digest.py` against `https://huggingface.co/<repo>/resolve/main/`; links to GitHub `blob/` pages give HTML, not media: use the `raw.githubusercontent.com` form.
- *Video samples* aren't supported: only still images (`img`, converted by `sips`) and audio (`aud`) are handled, and the page has no video player.
- *Changing a URL* for an existing position keeps the old file until `FORCE=1`.
- *Reordering items* shifts file names and the matching `captions` in `data/models.json`, since both go by list position.

After `make media`, run `make build` and commit the new files in `media/` together with `data/media.json` and `index.html`.
