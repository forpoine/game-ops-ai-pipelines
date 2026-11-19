"""Set C 정답 파일: 생성 지시값(1차 라벨)에 사용자가 확정한 값을 덮어쓴다. 전부 합성 데이터.
CONFIRMED = id: (category, severity). 사용자가 읽고 지시값 그대로 맞다고 한 행은 CONFIRMED_SAME에 id만 넣는다.
나머지는 label_status=generated(미확인). 원래 지시값은 orig_* 열에 남는다.
사용: python scripts/make_gold_c.py   결과 data/syn_voc_c_gold.csv"""
import csv, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
# 2026-11-18 사용자 확정: 손실 없는 튕김 4건은 S3가 아니라 S2("튕기는 거 S2로 업", Set C 4건만, 01 기준은 그대로). 규칙·대조 나머지 40건은 지시값 그대로.
CONFIRMED = {i: ("BUG", "S2") for i in ['SYNC-0036', 'SYNC-0054', 'SYNC-0056', 'SYNC-0074']}
CONFIRMED_SAME = set(['SYNC-0005', 'SYNC-0007', 'SYNC-0008', 'SYNC-0010', 'SYNC-0011', 'SYNC-0015', 'SYNC-0016', 'SYNC-0021', 'SYNC-0022', 'SYNC-0024', 'SYNC-0025', 'SYNC-0027', 'SYNC-0028', 'SYNC-0031', 'SYNC-0032', 'SYNC-0033', 'SYNC-0035', 'SYNC-0038', 'SYNC-0041', 'SYNC-0042', 'SYNC-0043', 'SYNC-0047', 'SYNC-0049', 'SYNC-0050', 'SYNC-0051', 'SYNC-0053', 'SYNC-0055', 'SYNC-0057', 'SYNC-0058', 'SYNC-0059', 'SYNC-0061', 'SYNC-0066', 'SYNC-0067', 'SYNC-0069', 'SYNC-0071', 'SYNC-0073', 'SYNC-0076', 'SYNC-0077', 'SYNC-0078', 'SYNC-0079'])
rows = list(csv.DictReader(open(ROOT/"data"/"syn_voc_c_generated.csv", encoding="utf-8-sig")))
cols = list(rows[0].keys()) + ["orig_category","orig_severity"]
with open(ROOT/"data"/"syn_voc_c_gold.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
    for r in rows:
        r["orig_category"], r["orig_severity"] = r["gold_category"], r["gold_severity"]
        if r["id"] in CONFIRMED:
            r["gold_category"], r["gold_severity"] = CONFIRMED[r["id"]]; r["label_status"] = "confirmed"
        elif r["id"] in CONFIRMED_SAME:
            r["label_status"] = "confirmed"
        w.writerow(r)
ch = [r for r in rows if r["id"] in CONFIRMED and (r["orig_category"], r["orig_severity"]) != CONFIRMED[r["id"]]]
print(len(rows), "rows; confirmed", len(CONFIRMED) + len(CONFIRMED_SAME), "; changed vs instruction", len(ch))
for r in ch: print(r["id"], r["orig_category"], r["orig_severity"], "->", CONFIRMED[r["id"]])
