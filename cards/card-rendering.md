# card-rendering

What `scripts/build.py` puts on each model card and section, and the limits it applies silently.

**Sections.** `GROUPS` in `build.py` lists every store type in page order with its heading, blurb and `tai` command. A store type missing from `GROUPS` is not rendered: the build prints `warning: <name> has type '<type>', which has no group in GROUPS`. When `tai download` shows a new type, add a `GROUPS` row (and a `USAGE` entry if `tai` can run it).

**One card, top to bottom:**
1. Name, licence chip (`hf.json` → `card.license`), store id.
2. `desc` and optional `note` from `data/models.json`.
3. Benchmarks: only the **first four** metrics with both `label` and `value`, plus a "Benchmarks: <host>" link to `source`. More than four in the data file are kept but not shown, so put the most telling ones first.
4. Samples (see below). A generating model with none gets "No samples on the model card".
5. "Try" example command, from `data/models.json` `usage` or the type default in `USAGE`.
6. Links (Hugging Face, or "Original on Hugging Face" when reached through an alias; `link` as "Demo page" or "Hugging Face (MLX)") and the copyable `tai download NAME` button.

**Generating models.** `GENERATORS` (Text-to-Image, Music Generation, Text-to-Speech, Image-to-3D) decides who gets a samples area. The same tuple is duplicated in `scripts/card_digest.py` (which prints media links only for those types); change both together. Text-to-Video is deliberately not in it: the page has no video samples, so video cards show no samples area.

**Samples on the page.** A sample shows only if `media/<slug>-<i>.jpg|mp3` exists, where `<i>` is its position in the `data/media.json` list and `slug` lowercases and turns non-alphanumerics into `-`. `captions[i]` in `models.json` pairs with the same position. Reordering or removing an item in `media.json` therefore shifts file names and captions: rerun `make media FORCE=1` (or rename the files) and fix `captions`.

**Search.** Each card carries `data-q` = name + store id + description, lowercased; the filter box matches against that only (not benchmarks or notes).

**Escaping.** Every data value goes through `esc()` (HTML-escaped, quotes included), so data files hold plain text, never HTML.

**Missing description.** A store model without a `models.json` entry still renders (empty description); `make check` / `make build` print it in `warning: no description …`.

**SWE-bench table.** `swe_html()` in `build.py` adds a last section (and nav chip) comparing every store model with a metric whose label matches `swe-?bench`, from all four metrics files and not only the first four shown on the card. Each distinct label is its own column, most common first, so "SWE-bench Pro" and "SWE-bench Pro v2" stay apart. To merge two, make their labels identical in the data. Rows sort by the first column, then the next, using the number in `value`. The filter box hides rows by model name, just as it hides cards. Clicking a column title sorts the table in the page's script (`table.swe` in `template.html`), using each cell's `data-v` number. Scores sort best-first and Model sorts A–Z, a second click flips the order, and missing scores stay last. Labels must match exactly, including case ("SWE-Bench" is a separate column from "SWE-bench").
