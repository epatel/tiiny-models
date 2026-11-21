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
    ("Music Generation", "Music", "Songs, loops and instrument samples.", None),
    ("Text-to-Speech", "Speech", "Text read aloud, voice cloning and voice design.", "tai tts"),
    ("Image-to-3D", "3D", "A textured 3D model from one picture.", "tai 3d"),
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
    "Text-to-Speech": 'tai tts -m {m} "Hello there, nice to meet you." --play',
    "Image-to-3D": "tai 3d -m {m} toy.png -o toy.glb",
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
