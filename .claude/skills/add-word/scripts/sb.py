# -*- coding: utf-8 -*-
"""Shared Supabase REST helpers for the add-word maintenance scripts.
Reads the secret key from env var SUPABASE_SECRET_KEY (never print it)."""
import json, os, sys, io, urllib.request, urllib.error, urllib.parse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = "https://gdqotnfcarjgfghourdm.supabase.co/rest/v1"
KEY = os.environ.get("SUPABASE_SECRET_KEY", "")
if not KEY:
    sys.exit("SUPABASE_SECRET_KEY is empty. Fill C:\\DEV\\env.bat and restart with cc.bat.")
Q = lambda s: urllib.parse.quote(s, safe="")


def req(method, path, body=None, prefer=None, rng=None):
    r = urllib.request.Request(BASE + path, method=method,
                               data=json.dumps(body).encode("utf-8") if body is not None else None)
    for k, v in {"apikey": KEY, "Authorization": "Bearer " + KEY, "Content-Type": "application/json",
                 "User-Agent": "word-atlas-admin-script/1.0"}.items():   # a custom UA is required
        r.add_header(k, v)
    if prefer: r.add_header("Prefer", prefer)
    if rng: r.add_header("Range", rng)
    try:
        raw = urllib.request.urlopen(r).read()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path} {e.code} {e.read().decode('utf-8', 'replace')}")
    return json.loads(raw) if raw else None


def all_(table, select="*", order="id"):
    """Page through a table (the project caps a response at 1000 rows)."""
    out, s = [], 0
    while True:
        rows = req("GET", f"/{table}?select={select}&order={order}", rng=f"{s}-{s + 999}")
        out += rows
        if len(rows) < 1000: return out
        s += 1000


def one(path):
    rows = req("GET", path + "&limit=1")
    return rows[0] if rows else None
