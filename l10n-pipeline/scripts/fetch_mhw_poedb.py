"""몬헌 월드 용어를 mhw.poedb.tw(팬 데이터 사이트) 목록 페이지에서 4개 언어로 받는다.
언어별 목록 페이지(eng/kor/jpn/spa)가 같은 번호(id)를 쓰므로 id로 묶는다. 페이지 12장만 요청.
원본은 cache/poedb/에 저장해 재사용. 결과: glossary/mhw_poedb_terms.csv (type,api_id,en,ko,ja,es,note)
ko는 사용자가 검수표(out/mhw_review.html)로 확인한 뒤에만 정답으로 쓴다.
실행: PYTHONIOENCODING=utf-8 python scripts/fetch_mhw_poedb.py
"""
import csv, html, re, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache" / "poedb"; CACHE.mkdir(parents=True, exist_ok=True)
LANGS = {"en": "eng", "ko": "kor", "ja": "jpn", "es": "spa"}
LISTS = {"item": ("items/item", "item"), "material": ("items/material", "item"), "monster": ("monsters/large", "monster")}


def page(code, path):
    f = CACHE / f"{code}_{path.replace('/', '_')}.html"
    if not f.exists():
        req = urllib.request.Request(f"https://mhw.poedb.tw/{code}/{path}", headers={"User-Agent": "curl/8.0 study-script"})
        f.write_bytes(urllib.request.urlopen(req, timeout=30).read()); time.sleep(1.5)
    return f.read_text(encoding="utf-8")


def names(code, path, kind):
    s = page(code, path)
    out = {}
    for m in re.finditer(rf"<a href='/{code}/{kind}/(\d+)/[^']*'>(.*?)</a>", s, re.S):
        t = html.unescape(re.sub(r"<[^>]+>", "", m.group(2))).strip()
        if t:
            out.setdefault(m.group(1), t)
    return out


rows = []
for typ, (path, kind) in LISTS.items():
    by = {lg: names(code, path, kind) for lg, code in LANGS.items()}
    for i, en in by["en"].items():
        if all(i in by[lg] for lg in LANGS):
            rows.append({"type": typ, "api_id": f"mhw-{typ}-{i}", "en": en, "ko": by["ko"][i], "ja": by["ja"][i], "es": by["es"][i], "note": "poedb"})
    print(typ, {lg: len(v) for lg, v in by.items()})

seen, uniq = set(), []
for r in rows:
    if r["en"].lower() in seen or "?" in r["en"]:
        continue
    seen.add(r["en"].lower()); uniq.append(r)
out = ROOT / "glossary" / "mhw_poedb_terms.csv"
with out.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(uniq[0])); w.writeheader(); w.writerows(uniq)
print("written", out.name, len(uniq))
