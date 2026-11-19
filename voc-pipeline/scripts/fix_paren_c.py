"""Set C 생성 글의 기계적 손질(2026-11-18, Claude, 사용자 부재 중). 합성 데이터.
재생성(괄호 금지 지시, 행마다 최대 3번씩)을 거쳐도 주제의 괄호 문구가 남은 7건만 고친다(규칙·대조 5건, 대조군 2건). 원칙:
- 괄호 안이 지시문을 그대로 옮긴 것(SYNC-0027)이거나 본문에 이미 있는 사실의 반복(SYNC-0054, 0001, 0045)이면 괄호째 지운다.
- 그 밖에는 괄호 기호만 지우고 문장은 그대로 둔다(사실이 글에 남도록).
고치기 전 원문은 data/syn_voc_c_generated_first.csv(첫 생성)와 data/regen_c.log(재생성)에 남아 있다.
사용: python scripts/fix_paren_c.py   (data/syn_voc_c_generated.csv를 덮어씀)"""
import csv, pathlib, re
ROOT = pathlib.Path(__file__).resolve().parent.parent
F = ROOT/"data"/"syn_voc_c_generated.csv"
DROP = {"SYNC-0027", "SYNC-0054", "SYNC-0001", "SYNC-0045"}  # 괄호째 삭제(0001·0045는 대조군 행, 주제 문구를 괄호로 옮김)
UNWRAP = {"SYNC-0024", "SYNC-0056", "SYNC-0071"}  # 괄호 기호만 삭제
rows = list(csv.DictReader(open(F, encoding="utf-8-sig"))); cols = list(rows[0].keys())
for r in rows:
    t0 = r["text"]
    if r["id"] in DROP:
        r["text"] = re.sub(r"\s*\([^)]*\)", "", t0)
    elif r["id"] in UNWRAP:
        r["text"] = re.sub(r"\s*\(([^)]*)\)", lambda m: " " + m.group(1), t0)
    r["text"] = re.sub(r"\s+", " ", r["text"]).strip()
    if r["text"] != t0: print(r["id"], "|", t0, "\n   ->", r["text"])
with open(F, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
