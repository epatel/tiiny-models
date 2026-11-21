"""Print a short digest of cached model cards: opening text and image/audio links.

Helps write data/models.json descriptions and pick samples for data/media.json.
Run scripts/fetch_hf.py first (it fills .cache/readme/).

    python3 scripts/card_digest.py              # every model
    python3 scripts/card_digest.py NAME ...     # only these
"""
import re
import sys

from common import CACHE, load, slug

GENERATORS = {"Text-to-Image", "Music Generation", "Text-to-Speech", "Image-to-3D"}


def text_of(md):
    md = re.sub(r"^---.*?\n---\n", "", md, flags=re.S)
    md = re.sub(r"<!--.*?-->|```.*?```", "", md, flags=re.S)
    md = re.sub(r"<[^>]+>", " ", md)
    md = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", md)
    md = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", md)
    paras = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", md)]
    return " ".join(p for p in paras if len(p) > 60 and not p.startswith(("#", "|")))[:500]


def media_links(md, hf_id):
    base = f"https://huggingface.co/{hf_id}/resolve/main/"
    urls = re.findall(r"!\[[^\]]*\]\(([^)\s]+)", md) + re.findall(r"<img[^>]+src=[\"']([^\"']+)", md)
    urls += re.findall(r"[\"'(]([^\"'()\s]+\.(?:wav|mp3|flac|ogg|m4a))", md)
    urls = [u if u.startswith("http") else base + u.lstrip("./") for u in urls]
    return [u for u in dict.fromkeys(urls) if "shields.io" not in u]


def main(only):
    for d in load("hf.json"):
        if only and d["name"] not in only:
            continue
        f = CACHE / "readme" / f"{slug(d['name'])}.md"
        md = f.read_text() if f.exists() else ""
        print(f"## {d['name']} [{d['type']}] hf={d['hf_id']} licence={(d.get('card') or {}).get('license')}")
        print("   ", text_of(md) or "(no card text)")
        if d["type"] in GENERATORS:
            print("    media:", media_links(md, d["hf_id"])[:10])


if __name__ == "__main__":
    main(set(sys.argv[1:]))
