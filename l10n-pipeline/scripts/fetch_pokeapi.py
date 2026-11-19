"""PokéAPI에서 아이템·종 이름(en/ko/ja/es)을 받아 glossary/pokeapi_terms.csv로 저장.
원본 응답은 cache/pokeapi/에 파일로 저장해 재사용한다. 텍스트 데이터만 사용.
실행: PYTHONIOENCODING=utf-8 python scripts/fetch_pokeapi.py
"""
import csv, json, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache" / "pokeapi"
OUT = ROOT / "glossary" / "pokeapi_terms.csv"
BASE = "https://pokeapi.co/api/v2"
HEADERS = {"User-Agent": "curl/8.0 study-script"}

# 아이템은 카테고리로 일반 소모품·상태이상 회복 위주, 종은 도감 번호 앞쪽
ITEM_CATEGORIES = ["healing", "status-cures", "pp-recovery", "revival", "vitamins",
                   "stat-boosts", "spelunking", "standard-balls", "special-balls",
                   "medicine", "picky-healing", "other"]
SPECIES_LIMIT = 400


def get(url: str, name: str):
    path = CACHE / name
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode("utf-8"))
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            return data
        except Exception as e:
            if attempt == 3:
                print("FAIL", url, e, file=sys.stderr)
                return None
            time.sleep(1.5 * (attempt + 1))


def pick(names, *langs):
    for lang in langs:
        for n in names:
            if n["language"]["name"] == lang:
                return n["name"]
    return ""


def row(kind, data):
    names = data.get("names", [])
    return {
        "type": kind,
        "api_id": data["name"],
        "en": pick(names, "en"),
        "ko": pick(names, "ko"),
        "ja": pick(names, "ja-Hrkt", "ja"),
        "es": pick(names, "es"),
        "note": f"pokeapi {kind} #{data['id']}",
    }


def main():
    item_urls = {}
    for cat in ITEM_CATEGORIES:
        d = get(f"{BASE}/item-category/{cat}", f"cat_{cat}.json")
        if not d:
            continue
        for it in d["items"]:
            item_urls[it["name"]] = it["url"]
    print("items:", len(item_urls))
    species_urls = {}
    d = get(f"{BASE}/pokemon-species?limit={SPECIES_LIMIT}", "species_index.json")
    for s in d["results"]:
        species_urls[s["name"]] = s["url"]
    print("species:", len(species_urls))

    jobs = [("item", n, u) for n, u in item_urls.items()] + \
           [("pokemon", n, u) for n, u in species_urls.items()]

    def work(j):
        kind, n, u = j
        sub = "item" if kind == "item" else "species"
        data = get(u, f"{sub}_{n}.json")
        return row(kind, data) if data else None

    with ThreadPoolExecutor(max_workers=8) as ex:
        rows = [r for r in ex.map(work, jobs) if r]

    # en/ko/ja/es 모두 있는 행만 측정용으로 사용
    full = [r for r in rows if r["en"] and r["ko"] and r["ja"] and r["es"]]
    seen, uniq = set(), []
    for r in full:  # 같은 영어명 중복(Legends Arceus 판 'la*' 등) 제거
        if r["en"] in seen:
            continue
        seen.add(r["en"])
        uniq.append(r)
    full = uniq
    dropped = len(rows) - len(full)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["type", "api_id", "en", "ko", "ja", "es", "note"])
        w.writeheader()
        w.writerows(full)
    print(f"saved {len(full)} rows (dropped {dropped} with missing language) -> {OUT}")


if __name__ == "__main__":
    main()
