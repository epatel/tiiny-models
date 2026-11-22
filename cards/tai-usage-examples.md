# tai-usage-examples

The "Try" command on each card: where it comes from and how it must track the `tai` CLI.

**Source of truth is the CLI, not this repo.** The `tai` CLI lives in `../tiiny-cli` (`src/tai/cli.py`, `src/tai/models.py`, README "Usage"). Its `TASK_BY_TYPE` in `models.py` maps a store type to a command: Text Generation and Image-Text-to-Text → `ask`/`chat`/`agent`, Text-to-Image → `image`, Text-to-Speech → `tts`, ASR → `asr`, Text Embedding → `embed`, Image-to-3D → `3d`, Text-to-Video → `video`, Music Generation → `music`. Types missing there (Image-to-Text/OCR, Text Reranking, Text Classification) have no command, so their cards show no example.

**How a card gets its command** (`usage_html` in `scripts/build.py`):
1. `usage` in that model's `data/models.json` entry, if set (a full command string), else
2. `USAGE[store type]` with `{m}` replaced by the store name, else
3. nothing.

`-m NAME` accepts the store display name (or any unique substring), so the full store name is always safe.

**When to set `usage`:** when the type default is wrong for the model. Current overrides:
- FLUX.2-klein editing LoRAs (Background-Remove, Object-Remove, Outpaint, Zoom) and FLUX.2-klein-4B itself: they edit a picture, so `tai image -i <file> "<instruction>"`. Outpaint expects a pure-green border and Zoom a red box drawn on the input.
- Qwen-Image-2.1-PE-T2I / PE-I2I: prompt enhancers listed as chat types; the example shows the short idea they expand.
- Qwen3-VoiceDesign-1.7B / CustomVoice: show the voice instruction (`-i "female, british accent"`).
- Z-Image-Turbo-CharacterDesignSheet: a prompt that triggers its LoRA.
- Foundation-1: makes instrument loops, not songs; `tai music` rejects `--lyrics`, `--instrumental` and `--style` for it, so the example is a prompt plus `--seconds`.
- AceStep-XL-Turbo: shows `--instrumental` and AceStep's own settings nested under `-x ace_step.…` (e.g. `ace_step.bpm=85`). The song default needs `-l lyrics.txt` because a song with vocals requires lyrics; YuE2 cannot do `--instrumental`.

**Rules:**
- Use only flags that exist in the CLI (`tai <cmd> --help`); don't invent options to make a model look better.
- Examples are illustrative inputs (`photo.jpg`, `recording.wav`), not claims about output quality; they are not run as part of the build.
- When `tai` gains a command for a new type, add a `USAGE` entry and the command to that type's `GROUPS` row; when a flag is renamed, grep `data/models.json` for `"usage"` too.
