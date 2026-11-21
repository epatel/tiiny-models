"""Look every store model up on Hugging Face.

Writes data/hf.json (repo id, licence, pipeline tag per model) and caches each model card in
.cache/readme/<slug>.md for scripts/card_digest.py. A store id with no Hugging Face page is looked
up under data/aliases.json (Tiiny's "-Turbo" builds and renamed models -> the original repo);
models with neither get search suggestions printed, so you can add an alias.

    python3 scripts/fetch_hf.py            # all models
    python3 scripts/fetch_hf.py NAME ...   # only these
"""
import json
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

from common import CACHE, get, load, save, slug, store


def lookup(row, aliases):
    name, typ, sid = row
    out = {"name": name, "type": typ, "id": sid, "hf_id": None, "via": None, "pipeline": None, "card": {}}
    for repo in [sid, aliases.get(sid)]:
        if not repo:
            continue
        status, text = get(f"https://huggingface.co/api/models/{repo}")
        if status != 200:
            continue
        j = json.loads(text)
        card = j.get("cardData") or {}
        out.update(hf_id=j["id"], via=repo if repo != sid else None, pipeline=j.get("pipeline_tag"),
                   card={k: card.get(k) for k in ("license", "base_model", "language")})
        _, readme = get(f"https://huggingface.co/{j['id']}/raw/main/README.md")
        (CACHE / "readme").mkdir(parents=True, exist_ok=True)
        (CACHE / "readme" / f"{slug(name)}.md").write_text(readme)
        break
    return out


def suggest(name, sid):
    q = urllib.parse.quote(sid.split("/")[-1].replace("-Turbo", ""))
    status, text = get(f"https://huggingface.co/api/models?search={q}&limit=5&sort=downloads")
    hits = [m["id"] for m in json.loads(text)] if status == 200 else []
    print(f"  {name}: no page for {sid}; candidates: {', '.join(hits) or 'none'}")


def main(only):
    aliases = load("aliases.json")
    rows = [r for r in store() if not only or r[0] in only]
    with ThreadPoolExecutor(8) as ex:
        found = list(ex.map(lambda r: lookup(r, aliases), rows))
    old = {d["name"]: d for d in load("hf.json")} if only else {}
    old.update({d["name"]: d for d in found})
    order = [r[0] for r in store()]
    save("hf.json", [old[n] for n in order if n in old])
    missing = [d for d in found if not d["hf_id"]]
    print(f"{len(found) - len(missing)} of {len(found)} found on Hugging Face")
    for d in missing:
        if d["id"] in aliases and aliases[d["id"]] is None:
            print(f"  {d['name']}: known to have no page (null in aliases.json)")
        else:
            suggest(d["name"], d["id"])


if __name__ == "__main__":
    main(set(sys.argv[1:]))
