"""pred_<tag>.csv를 data/syn_voc_gold.csv와 비교해 정확도 출력. 합성 데이터.
사용: python scripts/score.py gemma gptoss
전체 / 확정(label_status=confirmed) / 1차 라벨(generated) / ambiguous 제외 로 나눠 보고."""
import csv, sys, pathlib, collections
ROOT = pathlib.Path(__file__).resolve().parent.parent
gold = {r["id"]: r for r in csv.DictReader(open(ROOT/"data"/(__import__("os").environ.get("VOC_GOLD") or ("syn_voc_b_gold.csv" if __import__("os").environ.get("VOC_SET")=="b" else "syn_voc_gold.csv")), encoding="utf-8-sig"))}
def acc(rows, key, gk):
    return f"{sum(r[key]==gold[r['id']][gk] for r in rows)}/{len(rows)}" if rows else "-"
for tag in sys.argv[1:]:
    P = list(csv.DictReader(open(ROOT/"data"/f"pred_{tag}.csv", encoding="utf-8-sig")))
    groups = {"전체":P, "확정":[r for r in P if gold[r["id"]]["label_status"]=="confirmed"],
              "1차라벨":[r for r in P if gold[r["id"]]["label_status"]!="confirmed"],
              "ambiguous 제외":[r for r in P if gold[r["id"]]["ambiguous"]!="true"]}
    print(f"== {tag}  평균 {sum(float(r['sec']) for r in P)/len(P):.1f}초/건, 형식 실패 {sum(not r['pred_category'] for r in P)}건")
    for g, rows in groups.items():
        print(f"  {g:12} 카테고리 {acc(rows,'pred_category','gold_category')}  심각도 {acc(rows,'pred_severity','gold_severity')}  감성 {acc(rows,'pred_sentiment','gold_sentiment')}")
    for name, pk, gk in [("카테고리","pred_category","gold_category"),("심각도","pred_severity","gold_severity")]:
        c = collections.Counter((gold[r["id"]][gk], r[pk]) for r in P if r[pk]!=gold[r["id"]][gk])
        print(f"  오답 {name}(정답→예측):", ", ".join(f"{a}→{b} {n}" for (a,b),n in c.most_common(6)))
