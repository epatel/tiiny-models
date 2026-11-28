"""Build index.html from data/ and scripts/template.html (standard library only).

    python3 scripts/build.py
"""
import html
import json
import re

from common import DATA, ROOT, load, slug, store, store_date

GENERATORS = ("Text-to-Image", "Music Generation", "Text-to-Speech", "Image-to-3D")
GROUPS = [  # (store type, heading, what it's for, tai command)
    ("Text-to-Image", "Images", "Pictures from a prompt, and edits of pictures you give.", "tai image"),
    ("Music Generation", "Music", "Songs, loops and instrument samples.", "tai music"),
    ("Text-to-Speech", "Speech", "Text read aloud, voice cloning and voice design.", "tai tts"),
    ("Image-to-3D", "3D", "A textured 3D model from one picture.", "tai 3d"),
    ("Text-to-Video", "Video", "Short clips with sound, from a prompt or a start image.", "tai video"),
    ("Image-Text-to-Text", "Chat with vision", "Chat models that also read images.", "tai ask · tai chat · tai agent"),
    ("Text Generation", "Chat", "Text-only chat, reasoning and coding models.", "tai ask · tai chat · tai agent"),
    ("ASR", "Transcription", "Speech to text.", "tai asr"),
    ("Image-to-Text", "OCR and layout", "Text and structure out of scanned pages and photos.", None),
    ("Text Embedding", "Embeddings", "Vectors for search and RAG.", "tai embed"),
    ("Text Reranking", "Reranking", "Re-order search results by relevance.", None),
    ("Text Classification", "Classification", "Yes/no, choice and score answers about a text, as probabilities.", None),
]

USAGE = {  # example command per store type ({m} = model name); data/models.json "usage" overrides it
    "Text-to-Image": 'tai image -m {m} "a fox in the snow, watercolor" -o fox.png --open',
    "Music Generation": 'tai music -m {m} "synth-pop, female vocals" -l lyrics.txt -o song.mp3',
    "Text-to-Speech": 'tai tts -m {m} "Hello there, nice to meet you." --play',
    "Image-to-3D": "tai 3d -m {m} toy.png -o toy.glb",
    "Text-to-Video": 'tai video -m {m} "a paper boat drifting down a rainy street" -o boat.mp4 --open',
    "Image-Text-to-Text": 'tai ask -m {m} -f photo.jpg "what\'s in this picture?"',
    "Text Generation": 'tai ask -m {m} "explain RAII in two sentences"',
    "ASR": "tai asr -m {m} recording.wav",
    "Text Embedding": 'tai embed -m {m} "first text" "second text"',
}

MODELS = load("models.json")
MEDIA = load("media.json")
HF = {d["name"]: d for d in load("hf.json")}
METRICS = {}
for f in sorted((DATA / "metrics").glob("*.json")):
    METRICS.update(json.loads(f.read_text()))


def esc(s):
    return html.escape(str(s or ""), quote=True)


def metrics_html(name):
    m = METRICS.get(name) or {}
    rows = [x for x in m.get("metrics") or [] if x.get("label") and x.get("value")][:4]
    if not rows:
        return ""
    items = "".join(f'<div><dt>{esc(x["label"])}</dt><dd>{esc(x["value"])}'
                    + (f'<small>{esc(x["note"])}</small>' if x.get("note") else "") + "</dd></div>" for x in rows)
    src = m.get("source") or ""
    host = re.sub(r"^https?://(www\.)?([^/]+).*", r"\2", src)
    link = f'<a class="msrc" href="{esc(src)}">Benchmarks: {esc(host)}</a>' if src else ""
    return f'<dl class="metrics">{items}</dl>{link}'


def media_html(name):
    items, caps = MEDIA.get(name, []), MODELS.get(name, {}).get("captions", [])
    out = []
    for i, (kind, _url) in enumerate(items):
        f = ROOT / "media" / f"{slug(name)}-{i}.{'jpg' if kind == 'img' else 'mp3'}"
        if not f.exists():
            continue
        cap = caps[i] if i < len(caps) else ""
        if kind == "img":
            out.append(f'<figure><img src="media/{f.name}" alt="{esc(cap or "Sample from " + name)}" loading="lazy">'
                       + (f"<figcaption>{esc(cap)}</figcaption>" if cap else "") + "</figure>")
        else:
            out.append(f'<div class="clip"><span>{esc(cap or "Sample")}</span>'
                       f'<audio controls preload="none" src="media/{f.name}"></audio></div>')
    if not out:
        return ""
    return f'<div class="media {"imgs" if items[0][0] == "img" else "clips"}">{"".join(out)}</div>'


def usage_html(name, typ):
    cmd = MODELS.get(name, {}).get("usage") or USAGE.get(typ, "").format(m=name)
    if not cmd:
        return ""
    return (f'<div class="usage"><span>Try</span><button class="copy" type="button" data-cmd="{esc(cmd)}" '
            f'aria-label="Copy an example command for {esc(name)}">{esc(cmd)}</button></div>')


def card(name, typ, sid):
    info, hf = MODELS.get(name, {}), HF.get(name, {})
    hf_id, link = hf.get("hf_id"), info.get("link")
    links = []
    if hf_id:
        links.append(f'<a href="https://huggingface.co/{esc(hf_id)}">'
                     f'{"Original on Hugging Face" if hf.get("via") else "Hugging Face"}</a>')
    if link and link != f"https://huggingface.co/{hf_id}":
        links.append(f'<a href="{esc(link)}">{"Hugging Face (MLX)" if "huggingface.co" in link else "Demo page"}</a>')
    lic = (hf.get("card") or {}).get("license")
    gen = typ in GENERATORS
    m = media_html(name)
    if gen and not m:
        m = '<p class="nomedia">No samples on the model card' + (" · see the demo page" if link else "") + ".</p>"
    q = esc(f"{name} {sid} {info.get('desc', '')}".lower())
    return f"""<article class="card{' gen' if gen else ''}" id="{slug(name)}" data-q="{q}">
  <header><h3>{esc(name)}</h3>{f'<span class="lic">{esc(lic)}</span>' if lic else ''}</header>
  <code class="id">{esc(sid)}</code>
  <p>{esc(info.get('desc', ''))}</p>
  {f'<p class="note">{esc(info["note"])}</p>' if info.get("note") else ''}
  {metrics_html(name)}
  {m}
  {usage_html(name, typ)}
  <footer><div class="links">{' · '.join(links)}</div>
  <button class="copy" type="button" data-cmd="tai download {esc(name)}" aria-label="Copy the download command for {esc(name)}">tai download {esc(name)}</button></footer>
</article>"""


COMPARE = [  # comparison tables after the sections: (id, heading, blurb, columns)
    # columns: a regex (one column per distinct matching label) or [(column title, label regex), ...]
    ("swe-bench", "SWE-bench",
     "Every model above that reports a SWE-bench score, best first; click a column title to sort by it. "
     "Makers run these with different agent harnesses (noted under a score), so treat small gaps as noise; "
     "Turbo builds repeat their original's numbers.",
     r"(?i)swe-?bench"),
    ("knowledge", "Knowledge and reasoning",
     "Models that report the common knowledge and reasoning tests, without tools: MMLU-Pro, MMLU-Redux and MMLU "
     "(broad subject knowledge), GPQA and SuperGPQA (graduate-level science), and HLE, Humanity's Last Exam (expert questions). "
     "The maker's own label is shown under a score when it differs from the column title. Click a column title to sort.",
     [("MMLU-Pro", r"MMLU[- ]Pro"), ("MMLU-Redux", r"MMLU-Redux"), ("MMLU", r"MMLU"),
      ("GPQA", r"GPQA( Diamond)?( \(no tools\))?"), ("SuperGPQA", r"SuperGPQA"),
      ("HLE", r"(HLE|Humanity's Last Exam)( \(no tools\)| no tools| w/ CoT)?")]),
]


def num(v):
    m = re.search(r"\d+(\.\d+)?", v or "")
    return float(m.group()) if m else -1


def compare_html(rows, sid, head, blurb, spec):
    """A sortable table of the store models with a metric matching `spec` (see COMPARE)."""
    found = {}  # name -> {column: metric}
    for name, typ, _ in rows:
        for x in (METRICS.get(name) or {}).get("metrics") or []:
            label = x.get("label", "")
            if not x.get("value"):
                continue
            if isinstance(spec, str):
                col = label if re.search(spec, label) else None
            elif re.search(r"with tools|tools? not stated|likely with tools", x.get("note", "")):
                col = None  # named-column tables compare runs without tools only
            else:
                col = next((c for c, rx in spec if re.fullmatch(rx, label)), None)
            if col:
                found.setdefault(name, {}).setdefault(col, x)
    if not found:
        return "", 0
    if isinstance(spec, str):
        count = {}
        for d in found.values():
            for c in d:
                count[c] = count.get(c, 0) + 1
        cols = sorted(count, key=lambda c: (-count[c], c))
    else:
        cols = [c for c, _ in spec if any(c in d for d in found.values())]
    names = sorted(found, key=lambda n: [-num((found[n].get(c) or {}).get("value")) for c in cols])
    types = {r[0]: r[1] for r in rows}
    sortable = lambda label, i, cur="": (f'<th scope="col"{cur}><button type="button" data-col="{i}">{esc(label)}'
                                         '<span class="arrow" aria-hidden="true"></span></button></th>')
    heads = "".join(sortable(c, i + 1, ' aria-sort="descending"' if i == 0 else "") for i, c in enumerate(cols))
    body = []
    for n in names:
        cells = []
        for c in cols:
            x = found[n].get(c)
            if not x:
                cells.append('<td class="na">–</td>')
                continue
            notes = [x["label"]] if x["label"] != c and not isinstance(spec, str) else []
            notes += [x["note"]] if x.get("note") else []
            cells.append(f'<td data-v="{num(x["value"])}">{esc(x["value"])}'
                         + (f'<small>{esc(" · ".join(notes))}</small>' if notes else "") + "</td>")
        src = METRICS[n].get("source") or ""
        link = f'<a href="{esc(src)}">source</a>' if src else ""
        body.append(f'<tr data-q="{esc(n.lower())}"><th scope="row"><a href="#{slug(n)}">{esc(n)}</a>'
                    f'<span>{esc(types[n])}</span></th>{"".join(cells)}<td class="src">{link}</td></tr>')
    html_ = f"""<section id="{sid}" class="compare">
  <div class="sechead"><h2>{esc(head)}</h2><p>{esc(blurb)}</p><span class="type">{len(names)} models</span></div>
  <div class="tablewrap"><table class="cmp"><thead><tr>{sortable("Model", 0)}{heads}<th scope="col"><span class="sr">Source</span></th></tr></thead>
  <tbody>{"".join(body)}</tbody></table></div>
</section>"""
    return html_, len(names)


def main():
    rows = store()
    missing = [r[0] for r in rows if r[0] not in MODELS]
    if missing:
        print("warning: no description in data/models.json for:", ", ".join(missing))
    sections, nav = [], []
    for typ, head, what, cmd in GROUPS:
        group = [r for r in rows if r[1] == typ]
        if not group:
            continue
        sid = slug(head)
        nav.append(f'<a href="#{sid}">{esc(head)} <span>{len(group)}</span></a>')
        use = f" Use with <code>{esc(cmd)}</code>." if cmd else ""
        sections.append(f"""<section id="{sid}">
  <div class="sechead"><h2>{esc(head)}</h2><p>{esc(what)}{use}</p><span class="type">{esc(typ)} · {len(group)}</span></div>
  <div class="grid">{''.join(card(*r) for r in group)}</div>
</section>""")
    for sid, head, blurb, spec in COMPARE:
        table, n = compare_html(rows, sid, head, blurb, spec)
        if table:
            nav.append(f'<a href="#{sid}">{esc(head)} <span>{n}</span></a>')
            sections.append(table)
    known = {g[0] for g in GROUPS}
    for r in rows:
        if r[1] not in known:
            print(f"warning: {r[0]} has type {r[1]!r}, which has no group in GROUPS")
    n_media = sum(1 for r in rows if media_html(r[0]))
    n_metrics = sum(1 for r in rows if metrics_html(r[0]))
    page = (ROOT / "scripts" / "template.html").read_text()
    for key, value in {"NAV": "".join(nav), "SECTIONS": "\n".join(sections), "COUNT": len(rows),
                       "NMEDIA": n_media, "NMETRICS": n_metrics, "DATE": store_date()}.items():
        page = page.replace("{{" + key + "}}", str(value))
    (ROOT / "index.html").write_text(page)
    print(f"index.html: {len(rows)} models, {n_metrics} with benchmarks, {n_media} with samples")


if __name__ == "__main__":
    main()
