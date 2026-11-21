# committed-build

Decision: the built page (`index.html`, `media/`) is committed to `main`, and the build uses only the Python standard library.

**The choice.** `scripts/build.py` runs locally and its output is committed; GitHub Pages serves `main` as-is, with no Actions workflow and no package installs. Build scripts import nothing outside the standard library, so `make build` works on a stock macOS `python3` (3.9+) with no venv.

**Alternatives considered:**
- A GitHub Actions workflow that builds on push and deploys to Pages.
- A static-site generator or templating library (Jinja, a JS framework).
- Building at view time in the browser from the JSON files.

**Why this won:**
- The data changes by hand a few times a month; a local build plus one commit is the whole release.
- Nothing to install or keep updated, and nothing that can break the deploy when a dependency changes.
- The committed `index.html` diff shows exactly what readers will see, which makes review of number and text changes easy.
- One HTML file with inline CSS/JS loads fast and works without JavaScript except for the filter and copy buttons.

**Consequences.** Never hand-edit `index.html` (the next build overwrites it); commit it and `media/` in the same commit as the `data/` or `scripts/` change, or Pages shows stale content. `make media` is the one step with outside tools (`sips`, `ffmpeg`), and only for samples.

**When to revisit.** If several people edit the data at once (merge conflicts in the generated `index.html` become routine), if the build needs a library (e.g. image processing in Python), or if the page should rebuild on a schedule (store list fetched automatically).
