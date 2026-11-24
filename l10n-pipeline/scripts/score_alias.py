"""별명 채점(2026-11-24). 한국어 baseline 결과를 단계별로 다시 센다. API는 다시 부르지 않는다.
  1) 엄격: 지금 채점 그대로(월드 공식명 전체, 띄어쓰기만 무시)
  2) +기호: 하이픈·가운뎃점·괄호 등 기호 차이도 무시(조라-마그다라오스 = 조라 마그다라오스)
  3) +별명: 사용자가 '다른 시리즈 공식명'으로 판정한 표기도 정답
  엄격 점수에서 results/score_overrides.tsv에 적은 문장은 오답으로 뺀다(부분 일치의 허점, 예: '응급약 G').
  참고 칸 '다른 대상': 3)까지도 오답인 문장 중, 공식 용어지만 다른 대상·등급을 가리키는 표기를 쓴 문장 수
판정 파일: results/alias_judgments.tsv (n, api_id, 표기, 판정=별명|다른대상, 메모)
  n은 out/alias_list.txt의 줄 번호, api_id는 out/alias_list.json으로 맞춘다.
  근거 규칙: 정식 한국어판의 공식 용어만 별명으로 인정한다. 더블크로스(덥크) 한국어 패치는 유저 제작이라 근거로 쓰지 않는다.
사용: PYTHONIOENCODING=utf-8 python scripts/score_alias.py
"""
import csv, json, re
from measure import ROOT

MODELS = {"google_gemma-4-12b-qat": "Gemma", "openai_gpt-oss-20b": "gpt-oss", "qwen3-14b": "Qwen",
          "claude-haiku-5-5": "Haiku 5.5", "gemini-3.5-flash-lite": "Gemini Flash-Lite"}
SUFFIX = {"몬헌 틀": "_mhw", "공지체 틀": "_mhw_notice"}
JUDGE = ROOT / "results" / "alias_judgments.tsv"
OVERRIDE = ROOT / "results" / "score_overrides.tsv"  # 부분 일치로 정답이 됐지만 사람이 오답으로 판정한 문장
TPL = {"_mhw": "mhw", "_mhw_notice": "notice"}


def loose(s):
    return re.sub(r"[\s\-‐-―·・:()\[\]'\"!?.,~/]", "", s).lower()


aliases, other = {}, {}
if JUDGE.exists():
    for r in csv.DictReader(JUDGE.open(encoding="utf-8"), delimiter="\t"):
        {"별명": aliases, "다른대상": other}[r["판정"]].setdefault(r["api_id"], []).append(r["표기"])
wrong = set()
if OVERRIDE.exists():
    for r in csv.DictReader(OVERRIDE.open(encoding="utf-8"), delimiter="	"):
        wrong.add((r["model"], r["tpl"], int(r["id"])))
print("별명", sum(map(len, aliases.values())), "다른 대상", sum(map(len, other.values())))

print("| 모델 | 틀 | 엄격 | +기호 | +별명 | 다른 대상(오답 중) |")
print("|---|---|---|---|---|---|")
for m, name in MODELS.items():
    for tpl, suf in SUFFIX.items():
        rows = json.loads((ROOT / "results" / f"{m}_baseline{suf}.json").read_text(encoding="utf-8"))
        s1 = s2 = s3 = s4 = 0
        for r in rows:
            lg = r["langs"]["ko"]
            out, off = lg["out"], lg["official"]
            a = lg["match"] and (m, TPL[suf], r["id"]) not in wrong
            b = a or ((m, TPL[suf], r["id"]) not in wrong and loose(off) in loose(out))
            c = b or any(loose(x) in loose(out) for x in aliases.get(r["api_id"], []))
            d = not c and any(loose(x) in loose(out) for x in other.get(r["api_id"], []))
            s1 += a; s2 += b; s3 += c; s4 += d
        print(f"| {name} | {tpl} | {s1}/100 | {s2}/100 | {s3}/100 | {s4} |")
