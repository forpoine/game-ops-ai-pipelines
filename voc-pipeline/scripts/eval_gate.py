"""회귀 검사(eval gate): 프롬프트나 모델을 바꾼 결과(candidate)가 기준 결과(baseline)보다 나빠졌는지 확인한다. LLM 없음. 합성 데이터.

사용: python scripts/eval_gate.py <gold 파일> <baseline 태그> <candidate 태그> [--tol 0]
  예: python scripts/eval_gate.py syn_voc_gold_v3.csv gemma_cap2 gemma_cap2_schema
판정: 카테고리·심각도 정답 수가 tol보다 많이 줄거나 형식 실패가 늘면 FAIL(종료 코드 1).
      어느 쪽이든 맞던 글이 틀리게 바뀐 경우(flip)는 id별로 모두 출력한다. 점수가 같아도 flip은 사람이 봐야 한다.
배치 예: scripts/eval_all.sh 가 세 세트(A·B·C)를 차례로 검사한다.
"""
import csv, sys, pathlib, argparse

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIELDS = [("category", "pred_category", "gold_category"), ("severity", "pred_severity", "gold_severity")]


def load(name):
    return {r["id"]: r for r in csv.DictReader(open(ROOT / "data" / name, encoding="utf-8-sig"))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gold"); ap.add_argument("baseline"); ap.add_argument("candidate")
    ap.add_argument("--tol", type=int, default=0, help="허용하는 정답 수 감소(기본 0)")
    a = ap.parse_args()
    gold = load(a.gold)
    base, cand = load(f"pred_{a.baseline}.csv"), load(f"pred_{a.candidate}.csv")
    ids = [i for i in gold if i in base and i in cand]
    if len(ids) < len(gold):
        print(f"!! 예측이 없는 글 {len(gold) - len(ids)}건(비교에서 제외)")
    fail = False
    print(f"== {a.candidate} vs {a.baseline} ({a.gold}, {len(ids)}건)")
    for name, pk, gk in FIELDS:
        b = sum(base[i][pk] == gold[i][gk] for i in ids)
        c = sum(cand[i][pk] == gold[i][gk] for i in ids)
        bad = c < b - a.tol
        fail |= bad
        print(f"  {name:9} {b} -> {c} ({c - b:+d}) {'FAIL' if bad else 'ok'}")
        flips = [i for i in ids if base[i][pk] == gold[i][gk] and cand[i][pk] != gold[i][gk]]
        fixes = [i for i in ids if base[i][pk] != gold[i][gk] and cand[i][pk] == gold[i][gk]]
        for i in flips:
            print(f"    맞음->틀림 {i}: 정답 {gold[i][gk]}, 새 예측 {cand[i][pk] or '(형식 실패)'}")
        if fixes:
            print(f"    틀림->맞음 {len(fixes)}건: {', '.join(fixes[:10])}{' ...' if len(fixes) > 10 else ''}")
    fb = sum(not base[i]["pred_category"] for i in ids)
    fc = sum(not cand[i]["pred_category"] for i in ids)
    bad = fc > fb
    fail |= bad
    print(f"  형식 실패  {fb} -> {fc} ({fc - fb:+d}) {'FAIL' if bad else 'ok'}")
    if "needs_review" in next(iter(cand.values()), {}):
        print(f"  사람 검수로 넘긴 글(needs_review) {sum(cand[i].get('needs_review') == '1' for i in ids)}건")
    print("RESULT:", "FAIL" if fail else "PASS")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
