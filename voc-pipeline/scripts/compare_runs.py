"""같은 조건으로 두 번 돌린 예측의 흔들림(실행 간 차이)을 잰다. 합성 데이터. LM Studio 불필요.
사용: python scripts/compare_runs.py <정답파일명> <tag1> <tag2>   예: compare_runs.py syn_voc_gold_v3.csv gptoss_cap2 gptoss_cap2_r2
출력: 카테고리·심각도·감성이 두 실행에서 달라진 행 수, 각 실행의 정확도(심각도)."""
import csv, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
g, t1, t2 = sys.argv[1:4]
gold = {r["id"]: r for r in csv.DictReader(open(ROOT/"data"/g, encoding="utf-8-sig"))}
A = {r["id"]: r for r in csv.DictReader(open(ROOT/"data"/f"pred_{t1}.csv", encoding="utf-8-sig"))}
B = {r["id"]: r for r in csv.DictReader(open(ROOT/"data"/f"pred_{t2}.csv", encoding="utf-8-sig"))}
ids = [i for i in A if i in B]
for k in ("pred_category", "pred_severity", "pred_sentiment"):
    print(f"  {k}: {len(ids)}건 중 두 실행이 다른 행 {sum(A[i][k] != B[i][k] for i in ids)}건")
for t, P in ((t1, A), (t2, B)):
    print(f"  {t}: 심각도 {sum(P[i]['pred_severity'] == gold[i]['gold_severity'] for i in ids)}/{len(ids)}, 카테고리 {sum(P[i]['pred_category'] == gold[i]['gold_category'] for i in ids)}/{len(ids)}")
