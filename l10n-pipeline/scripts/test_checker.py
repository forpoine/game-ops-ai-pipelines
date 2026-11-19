"""검수기 자체 테스트: 깨끗한 합성 문장 3개 + 심은 오류 10개 검출률.
픽스처는 검수기 동작 확인용 손작성 문장(공지 본문 아님, 일본어는 사람 검증 안 함).
실행: PYTHONIOENCODING=utf-8 python scripts/test_checker.py
"""
import copy
from checker import check_notice, load_glossary

G = load_glossary()

CLEAN = [
    {"id": "A", "en": "Each trainer receives 3 Potion at 10:00 on 2026-12-01.",
     "terms": ["potion"],
     "tr": {"ko": "트레이너 한 명당 2026-12-01 10:00에 상처약 3개를 받습니다.",
            "ja": "トレーナー1人につき2026-12-01 10:00にキズぐすりを3個受け取れます。",
            "es": "Cada entrenador recibe 3 Poción a las 10:00 del 2026-12-01."}},
    {"id": "B", "en": "Full Restore drop rates: 40%, 35%, 25%.",
     "terms": ["full-restore"], "prob": True,
     "tr": {"ko": "회복약 드롭 확률: 40%, 35%, 25%.",
            "ja": "かいふくのくすりのドロップ確率: 40%, 35%, 25%。",
            "es": "Probabilidades de Restaurar Todo: 40%, 35%, 25%."}},
    {"id": "C", "en": "Buy Potion for 200 coins, up to 5 per day.",
     "terms": ["potion"],
     "tr": {"ko": "상처약을 200코인에 하루 최대 5개까지 살 수 있습니다.",
            "ja": "キズぐすりを200コインで、1日に最大5個まで購入できます。",
            "es": "Compra Poción por 200 monedas, hasta 5 al día."}},
]
LIMITS = {"ko": 60, "ja": 60, "es": 80}


def base(i):
    return copy.deepcopy(next(c for c in CLEAN if c["id"] == i))


def planted():
    """(설명, 기대 종류, 변형된 공지)"""
    out = []
    def mut(desc, kind, i, fn):
        n = base(i); fn(n); out.append((desc, kind, n))
    mut("ko 용어를 일반 번역(포션)으로", "term", "A", lambda n: n["tr"].__setitem__("ko", n["tr"]["ko"].replace("상처약", "포션")))
    mut("ja 용어를 ポーション으로", "term", "A", lambda n: n["tr"].__setitem__("ja", n["tr"]["ja"].replace("キズぐすり", "ポーション")))
    mut("es 용어를 Poción 아닌 Pocion(악센트 누락)으로", "term", "A", lambda n: n["tr"].__setitem__("es", n["tr"]["es"].replace("Poción", "Pocion")))
    mut("ko 개수 3 -> 5", "number", "A", lambda n: n["tr"].__setitem__("ko", n["tr"]["ko"].replace("3개", "5개")))
    mut("ja 시각 10:00 -> 11:00", "number", "A", lambda n: n["tr"].__setitem__("ja", n["tr"]["ja"].replace("10:00", "11:00")))
    mut("es 날짜 12-01 -> 12-10", "number", "A", lambda n: n["tr"].__setitem__("es", n["tr"]["es"].replace("12-01", "12-10")))
    mut("ko 가격 200 -> 20", "number", "C", lambda n: n["tr"].__setitem__("ko", n["tr"]["ko"].replace("200", "20")))
    mut("ja 번역 누락(빈 문자열)", "missing", "C", lambda n: n["tr"].__setitem__("ja", ""))
    mut("es 칸에 한국어가 들어감", "missing", "C", lambda n: n["tr"].__setitem__("es", n["tr"]["ko"]))
    mut("ko 확률 합 100 -> 95(25 -> 20)", "prob", "B", lambda n: n["tr"].__setitem__("ko", n["tr"]["ko"].replace("25%", "20%")))
    mut("es 자리표시자 [[T1]] 잔존", "leftover", "C", lambda n: n["tr"].__setitem__("es", n["tr"]["es"].replace("Poción", "[[T1]]")))
    mut("ko 글자 넘침(60자 초과)", "overflow", "C", lambda n: n["tr"].__setitem__("ko", n["tr"]["ko"] + " 많이 많이 많이 많이 많이 많이 많이 많이 많이 많이 많이"))
    return out


def main():
    print("== 깨끗한 문장(오탐 확인)")
    fp = 0
    for c in CLEAN:
        iss = check_notice(c, G, LIMITS)
        fp += len(iss)
        print(c["id"], "이슈", len(iss), iss if iss else "")
    print("오탐", fp, "건\n== 심은 오류")
    caught = 0
    cases = planted()
    for desc, kind, n in cases:
        iss = check_notice(n, G, LIMITS)
        hit = any(x["kind"] == kind for x in iss)
        caught += hit
        print("검출" if hit else "놓침", "|", kind, "|", desc, "|", [x["kind"] for x in iss])
    print(f"== 검출 {caught}/{len(cases)}, 오탐 {fp}")


if __name__ == "__main__":
    main()
