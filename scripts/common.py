"""Shared paths and helpers (standard library only)."""
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CACHE = ROOT / ".cache"
UA = {"User-Agent": "tiiny-models-catalog"}


def store():
    """Rows of data/store.txt as (name, type, id); '#' lines are comments."""
    rows = []
    for line in (DATA / "store.txt").read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            rows.append(tuple(line.split("|")))
    return rows


def store_date():
    m = re.search(r"Updated: (\S+)", (DATA / "store.txt").read_text())
    return m.group(1) if m else ""


def load(name):
    return json.loads((DATA / name).read_text())


def save(name, value):
    (DATA / name).write_text(json.dumps(value, indent=1, ensure_ascii=False) + "\n")


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def get(url):
    """(status, text) for a URL; never raises on HTTP errors."""
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
