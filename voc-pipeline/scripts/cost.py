"""상용 API 예측 파일의 토큰 합계와 비용(토큰 x 단가)을 계산한다. 단가는 인자로 받는다(코드에 박지 않음, 출처와 날짜를 함께 기록할 것).
사용: python scripts/cost.py <tag> <입력 $/1M> <출력 $/1M> [--scale 10000]
  --scale: 하루 N건 처리 시 추정 비용(같은 평균 토큰 가정, 추정치)
"""
import csv, pathlib, sys, argparse

ROOT = pathlib.Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("tag"); ap.add_argument("pin", type=float); ap.add_argument("pout", type=float)
ap.add_argument("--scale", type=int, default=10000)
a = ap.parse_args()
P = list(csv.DictReader(open(ROOT / "data" / f"pred_{a.tag}.csv", encoding="utf-8-sig")))
tin = sum(int(r["in_tok"]) for r in P); tout = sum(int(r["out_tok"]) for r in P)
usd = tin / 1e6 * a.pin + tout / 1e6 * a.pout
sec = sorted(float(r["sec"]) for r in P)
print(f"== {a.tag}: {len(P)}건, 입력 {tin:,} / 출력 {tout:,} 토큰(실측), 비용 ${usd:.4f}(실측 토큰 x 단가)")
print(f"  건당 평균 입력 {tin / len(P):.0f} / 출력 {tout / len(P):.0f} 토큰, 지연 중앙값 {sec[len(sec) // 2]:.2f}초, 최대 {sec[-1]:.2f}초")
print(f"  하루 {a.scale:,}건이면 약 ${usd / len(P) * a.scale:.2f}/일 (추정: 같은 평균 토큰 가정)")
print(f"  사람 검수로 넘긴 글 {sum(r['needs_review'] == '1' for r in P)}건")
