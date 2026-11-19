"""results/*.json을 읽어 모델·방식별 공식 표기 일치율 표를 출력한다.
실행: PYTHONIOENCODING=utf-8 python scripts/summarize.py
protected의 일치는 '자리표시자를 그대로 유지했는가'이므로, 치환 후 공식명이 들어가는 것은 구조상 보장된다.
"""
import json
from pathlib import Path

RES = Path(__file__).resolve().parent.parent / "results"
LANGS = ["ko", "ja", "es"]

for p in sorted(RES.glob("*.json")):
    rows = json.loads(p.read_text(encoding="utf-8"))
    print(f"\n== {p.stem} (n={len(rows)})")
    for kind in (None, "item", "pokemon"):
        sub = [r for r in rows if kind in (None, r["type"])]
        cells = []
        for lg in LANGS:
            m = sum(r["langs"][lg]["match"] for r in sub)
            cells.append(f"{lg} {m}/{len(sub)} ({100*m/len(sub):.0f}%)" if sub else f"{lg} -")
        print(f"  {kind or 'all':8s} " + "  ".join(cells))
