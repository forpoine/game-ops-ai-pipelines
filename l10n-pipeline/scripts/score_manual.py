"""수작업 시험지 채점. 사용자가 붙여 준 결과 글을 파일 또는 인자로 받는다.
형식 예: "시간 03:12.3 (192초)\n체크: 문장3 ja, 문장7 es"
실행: PYTHONIOENCODING=utf-8 python scripts/score_manual.py "결과 글 통째로"   (또는 --file 결과.txt)
출력: 사람 검출/놓침/오탐 + 검수기와 같은 기준 비교 + 소요 시간 비교.
검출 기준: 심은 오류가 있는 (문장, 언어) 칸에 체크하면 검출. 정답이 아닌 칸에 체크하면 오탐.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
text = Path(sys.argv[2]).read_text(encoding="utf-8") if len(sys.argv) > 2 and sys.argv[1] == "--file" else " ".join(sys.argv[1:])
import os
key = json.loads(Path(os.environ.get("KEY_PATH") or ROOT / "out" / "manual_answer_key.json").read_text(encoding="utf-8"))

m = re.search(r"\((\d+)초\)", text)
secs = int(m.group(1)) if m else None
checked = {(int(n), lg) for n, lg in re.findall(r"문장\s*(\d+)\s*(ko|ja|es)", text, re.I) for lg in [lg.lower()]}

planted = {it["no"]: it["planted"] for it in key["items"] if it["planted"]}
truth = {(no, p["lang"]) for no, p in planted.items()}
hit = checked & truth
miss = truth - checked
fp = checked - truth

# 검수기 기준(같은 정답 기준: 심은 칸에서 같은 언어 플래그가 났는가 / 정상 칸에서 플래그가 났는가)
ck_hit = ck_fp = 0
for it in key["items"]:
    flagged_langs = {f.split(":")[0] for f in it["checker_flags"]}
    if it["planted"]:
        ck_hit += it["planted"]["lang"] in flagged_langs
    else:
        ck_fp += len(flagged_langs)

print(f"사람: 검출 {len(hit)}/{len(truth)}, 놓침 {len(miss)}, 오탐(정답 아닌 칸 체크) {len(fp)}")
for no, lg in sorted(miss):
    p = planted[no]; print(f"  놓침: 문장{no} {lg} [{p['kind']}] {p['desc']}")
for no, lg in sorted(fp):
    print(f"  오탐: 문장{no} {lg}")
print(f"검수기: 검출 {ck_hit}/{len(truth)}, 정상 문장 오탐 {ck_fp}건")
if secs is not None:
    ms = key["checker_ms_for_15"]
    print(f"시간: 사람 {secs}초, 검수기 {ms}ms (약 {secs*1000/ms:,.0f}배)")
else:
    print("시간을 찾지 못함: '(NNN초)' 형식이 있어야 함")
