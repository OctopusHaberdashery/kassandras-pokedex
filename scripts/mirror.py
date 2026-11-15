#!/usr/bin/env python3
"""Make the website's daily copy of the Pokémon card data from tcgcsv.com.

tcgcsv doesn't let web pages download from it directly (and asks apps not to), so a GitHub job runs this
once a day and the app reads the copy from its own website instead. Following tcgcsv's rules:
  * a custom User-Agent on every request and a short pause between requests
  * check last-updated.txt first and do nothing if our copy is already current
  * keep only what the app uses

Usage: python3 scripts/mirror.py DATA_DIR
Writes DATA_DIR/groups.json, DATA_DIR/<groupId>/products.json and prices.json, and DATA_DIR/updated.txt.
Prints complete=true|false for the workflow (false = some sets failed; they keep their previous copy).
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

ROOT = os.environ.get("TCGCSV_ROOT", "https://tcgcsv.com/")   # (changed only for testing)
BASE = ROOT + "tcgplayer/3/"          # category 3 = Pokémon (English)
STAMP_URL = ROOT + "last-updated.txt"
UA = "KassandrasPokedex/1.0 (+https://github.com/OctopusHaberdashery/kassandras-pokedex; one daily mirror)"
PAUSE = 0.15
KEEP = {"Number", "Rarity", "Card Type", "Stage"}


def get(url, tries=4):
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json, text/plain"})
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read().decode("utf-8")
            time.sleep(PAUSE)
            return body
        except urllib.error.HTTPError as e:
            if e.code < 500 and e.code != 429:
                raise
            wait = 30 if e.code == 429 else 5 * (attempt + 1)
        except (urllib.error.URLError, TimeoutError):
            wait = 5 * (attempt + 1)
        print(f"  retrying {url} in {wait}s", flush=True)
        time.sleep(wait)
    raise RuntimeError("gave up on " + url)


def write(path, results):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"results": results}, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, path)


def slim_group(g):
    return {k: g.get(k) for k in ("groupId", "name", "abbreviation", "publishedOn")}


def slim_product(p):
    return {"productId": p.get("productId"), "name": p.get("name") or "",
            "extendedData": [{"name": e.get("name"), "value": e.get("value")}
                             for e in p.get("extendedData") or [] if e.get("name") in KEEP]}


def slim_price(p):
    return {"productId": p.get("productId"), "subTypeName": p.get("subTypeName"), "marketPrice": p.get("marketPrice")}


def main(out):
    os.makedirs(out, exist_ok=True)
    stamp = get(STAMP_URL).strip()
    stamp_file = os.path.join(out, "updated.txt")
    previous = open(stamp_file).read().strip() if os.path.exists(stamp_file) else ""
    if previous == stamp and os.path.exists(os.path.join(out, "groups.json")):
        print(f"Already have tcgcsv's {stamp} data; nothing to download.")
        print("complete=true")
        return

    print(f"tcgcsv updated {stamp} (our copy: {previous or 'none'}); downloading.", flush=True)
    groups = json.loads(get(BASE + "groups"))["results"]
    write(os.path.join(out, "groups.json"), [slim_group(g) for g in groups])
    failed = []
    for i, g in enumerate(groups, 1):
        gid = g["groupId"]
        try:
            products = json.loads(get(f"{BASE}{gid}/products"))["results"]
            prices = json.loads(get(f"{BASE}{gid}/prices"))["results"]
            write(os.path.join(out, str(gid), "products.json"), [slim_product(p) for p in products])
            write(os.path.join(out, str(gid), "prices.json"), [slim_price(p) for p in prices])
        except Exception as e:  # keep yesterday's copy of this set and carry on
            failed.append(gid)
            print(f"  set {gid} failed: {e}", flush=True)
        if i % 25 == 0:
            print(f"  {i}/{len(groups)} sets", flush=True)

    print(f"Done: {len(groups) - len(failed)}/{len(groups)} sets.")
    if failed:
        print("complete=false")      # don't record the stamp, so the next run tries again
    else:
        with open(stamp_file, "w") as f:
            f.write(stamp + "\n")
        print("complete=true")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data")
