"""실제 번역 결과(notices/translated_<model>.json)에 오류 10개를 심어 검수기 검출률을 잰다. LLM 없음.
글자 수 한도는 Photoshop 수치가 아직 없어 가정값: es는 영어 길이의 1.3배, ja는 한국어 길이의 1.3배.
실행: PYTHONIOENCODING=utf-8 python scripts/plant_errors.py [모델파일명]
"""
import copy, json, sys
from pathlib import Path
from checker import ROOT, load_glossary, check_notice
from report import write_report

G = load_glossary()
name = sys.argv[1] if len(sys.argv) > 1 else "translated_google_gemma-4-12b-qat.json"
CLEAN = json.loads((ROOT / "notices" / name).read_text(encoding="utf-8"))
KO_LEN = {}


def _caps():
    """Photoshop 실측(results/ps_measure.json)에서 추정한 본문 영역(880x520px, 28px) 최대 글자 수. 없으면 가정값."""
    p = ROOT / "results" / "ps_measure.json"
    return json.loads(p.read_text(encoding="utf-8"))["estimated_capacity_chars"] if p.exists() else None


def limits_for(n):
    c = _caps()
    if c:
        return {"ko": c["ko"], "ja": c["ja"], "es": c["es"]}
    return {"ko": 400, "ja": int(len(n["tr"]["ko"]) * 1.3), "es": int(len(n["en"]) * 1.3)}


def get(i):
    return copy.deepcopy(next(c for c in CLEAN if c["id"].startswith(i)))


def sub(n, lg, a, b):
    assert a in n["tr"][lg], (n["id"], lg, a)
    n["tr"][lg] = n["tr"][lg].replace(a, b)


# (설명, 기대 종류, 기대 언어, 공지 id 접두, 변형)
PLANTS = [
    ("ja 용어를 영어 직역으로", "term", "ja", "N1", lambda n: sub(n, "ja", "回復薬グレート", "ポーション")),
    ("es 용어 표기 변경(Ultra Ball -> Ultra Bola)", "term", "es", "N3", lambda n: sub(n, "es", "Ultra Ball", "Ultra Bola")),
    ("ja 보상 만료일 14일 -> 7일", "number", "ja", "N4", lambda n: sub(n, "ja", "14日", "7日")),
    ("es 점검 날짜 12-03 -> 12-30", "number", "es", "N1", lambda n: sub(n, "es", "2026-12-03", "2026-12-30")),
    ("ja 출현 시각 20:00 -> 21:00", "number", "ja", "N3", lambda n: sub(n, "ja", "20:00", "21:00")),
    ("es 번역 통째로 누락", "missing", "es", "N2", lambda n: n["tr"].__setitem__("es", "")),
    ("es 칸에 한국어가 들어감", "missing", "es", "N4", lambda n: n["tr"].__setitem__("es", n["tr"]["ko"])),
    ("ja 확률 30% -> 20%(합 90%)", "prob", "ja", "N5", lambda n: sub(n, "ja", "30%", "20%")),
    ("es 자리표시자 잔존", "leftover", "es", "N5", lambda n: sub(n, "es", "Gema de wyvern", "[[T1]]")),
    ("ja 글자 넘침(한도 초과)", "overflow", "ja", "N3", lambda n: n["tr"].__setitem__("ja", n["tr"]["ja"] + "このイベントの詳細についてはゲーム内のお知らせをご確認ください。" * (limits_for(n)["ja"] // 30 + 1))),
    ("ja 번역 안 된 영어 단어 남음(メンテナンス -> maintenance)", "english", "ja", "N1", lambda n: sub(n, "ja", "メンテナンス", "maintenance")),
]


def main():
    print("== 원본(심기 전) 검수 결과: 이슈가 나오면 실제 번역의 문제인지 오탐인지 사람이 확인")
    fp = 0
    for n in CLEAN:
        iss = check_notice(n, G, limits_for(n))
        fp += len(iss)
        print(n["id"], len(iss), iss or "")
    print(f"원본 이슈 {fp}건\n== 심은 오류 {len(PLANTS)}개")
    caught, mutated = 0, []
    for desc, kind, lg, nid, fn in PLANTS:
        n = get(nid); fn(n)
        iss = check_notice(n, G, limits_for(n))
        hit = any(x["kind"] == kind and x["lang"] == lg for x in iss)
        caught += hit
        n["id"] = f"[심은오류 {kind}] {desc} ({n['id']})"
        mutated.append(n)
        print("검출" if hit else "놓침", "|", kind, lg, "|", desc, "|", sorted({f"{x['lang']}:{x['kind']}" for x in iss}))
    print(f"== 검출 {caught}/{len(PLANTS)}, 원본 이슈 {fp}건(확인: 번역에 영어가 실제로 남아 있어 오탐 아님)")
    write_report(CLEAN + mutated, G, limits_for, ROOT / "out" / "report_planted.html")


if __name__ == "__main__":
    main()
