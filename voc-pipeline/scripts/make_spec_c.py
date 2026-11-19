"""Set C 지시표(80건, 2026-11-18): 심각도 경계 규칙(01, cap2)의 일반화 확인용 보류 세트. 규칙을 뽑을 때 보지 않은 새 글. 전부 합성.
구성(사용자 선택 '새 상황 위주'): 규칙 범위 안 새 상황 9주제, 규칙 조건이 빠진 대조 2주제, 규칙과 무관한 9주제, 주제마다 4건.
A·B와 다른 점: 주제마다 심각도를 01 기준으로 하나만 고정하고(주제 안 무작위 정답 방지), 심각도를 가르는 사실을 주제 문장에 적는다.
급증 없음, 판단이 갈리게 섞는 행(ambiguous) 없음. 설계 값이며 측정값이 아니다. random seed 고정. 서비스명은 {SERVICE}.
출력: data/syn_voc_c_spec.csv (B의 열 + scope: rule | contrast | control)"""
import csv, random, datetime as dt, pathlib

random.seed(23)
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "syn_voc_c_spec.csv"
PER_TOPIC = 4
# (category, 주제 문장, cluster, 심각도(01 기준 고정), scope)
TOPICS = [
 # 규칙 범위 안 새 상황
 ("BAL", "레이드 보스가 너무 어려워 몇 주째 공략이 막혀 더 진행을 못 함", "c_raid_hard", "S3", "rule"),
 ("BAL", "새로 열린 지역 몬스터가 너무 약해서 긴장감이 없다는 취향 의견", "c_zone_easy", "S4", "rule"),
 ("MON", "시즌 패스 보상 구성이 가격에 비해 아쉬움(보상 목록은 구매 전에 공개돼 있었고 받은 것도 목록 그대로)", "c_pass_value", "S4", "rule"),
 ("MON", "멤버십 혜택이 기대보다 적음(혜택 안내는 가입 전에 공개돼 있었고 안내대로 받고 있음)", "c_member_value", "S4", "rule"),
 ("MON", "시즌 패스 보상이 상점 안내에 표시된 수량보다 적게 지급됨", "c_pass_mismatch", "S2", "rule"),
 ("OPS", "출석 체크를 다 했는데 출석 보상이 우편함에 들어오지 않음", "c_attend_missing", "S2", "rule"),
 ("BUG", "던전을 클리어한 직후 게임이 튕겨서 클리어 기록과 보상이 사라짐", "c_crash_loss", "S2", "rule"),
 ("BUG", "시즌 미션을 다 했는데 완료 처리가 안 돼 시즌 보상을 못 받음", "c_mission_unmarked", "S2", "rule"),
 ("OPS", "공식 예고 영상에서 보여 준 기능이 실제 업데이트에는 빠져 있어 기대와 다름", "c_preview_mismatch", "S3", "rule"),
 # 규칙의 조건이 빠진 대조(규칙을 지나치게 넓혀 적용하는지 확인)
 ("BUG", "게임이 자주 튕기지만 다시 접속하면 진행과 보상은 그대로 남아 있음(손실 없음)", "c_crash_noloss", "S3", "contrast"),
 ("BUG", "업적 조건을 채웠는데 업적 완료 표시가 안 뜸(게임 진행과 보상에는 지장 없음)", "c_achv_unmarked", "S3", "contrast"),
 # 규칙과 무관한 주제(A·B와 같은 주제의 새 글)
 ("BUG", "로그인이 안 됨, 접속 불가", "login_fail", "S2", "control"),
 ("BUG", "결제 후 재화가 들어오지 않음", "payment_missing", "S2", "control"),
 ("BUG", "로딩 화면에서 멈춰 진행 불가", "loading_stuck", "S2", "control"),
 ("BAL", "특정 캐릭터가 너무 강함", "bal_strong_char", "S3", "control"),
 ("BAL", "매칭에서 실력 차가 큼", "bal_matching", "S3", "control"),
 ("MON", "확률 조작 의혹 제기", "mon_rate_suspect", "S2", "control"),
 ("COM", "채팅 욕설 신고", "com_abuse", "S3", "control"),
 ("COM", "거래 사기 피해 제보", "com_scam", "S2", "control"),
 ("ETC", "새 콘텐츠 제안", "etc_suggest", "S4", "control"),
]
SENT = {"BUG": ["neg","neg","neu"], "BAL": ["neg","neg","neu"], "MON": ["neg","neg","neu"],
        "OPS": ["neg","neu"], "COM": ["neg","neu"], "ETC": ["pos","neu","pos"]}
LANGS = ["ko"] * 67 + ["en"] * 17 + ["mixed"] * 16
STYLES = ["짧은 반말", "정중한 존댓말", "감정이 격한 말투", "건조한 보고체", "푸념하듯 늘어지는 말투"]
LENS = ["1문장", "1~2문장", "2~3문장"]
START = dt.datetime(2026, 5, 4, 0, 0)  # 합성 날짜(실제 사건 아님)
rows = []
for cat, seed, cl, sev, scope in TOPICS:
    for _ in range(PER_TOPIC):
        rows.append(dict(gold_category=cat, seed=seed, gold_cluster=cl, gold_severity=sev, scope=scope,
                         gold_sentiment=random.choice(SENT[cat]), day=random.randint(0, 6)))
for r in rows:
    r["lang"] = random.choice(LANGS); r["style"] = random.choice(STYLES); r["length"] = random.choice(LENS)
    r["ts"] = (START + dt.timedelta(days=r["day"], hours=random.randint(0, 23), minutes=random.randint(0, 59))).strftime("%Y-%m-%d %H:%M")
rows.sort(key=lambda r: r["ts"])
cols = ["id","ts","lang","style","length","gold_category","gold_severity","gold_sentiment","gold_cluster","ambiguous","secondary_category","scope","seed"]
with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
    for i, r in enumerate(rows, 1):
        w.writerow(dict(id=f"SYNC-{i:04d}", ts=r["ts"], lang=r["lang"], style=r["style"], length=r["length"],
            gold_category=r["gold_category"], gold_severity=r["gold_severity"], gold_sentiment=r["gold_sentiment"],
            gold_cluster=r["gold_cluster"], ambiguous="false", secondary_category="", scope=r["scope"], seed=r["seed"]))
from collections import Counter
print(len(rows), "rows ->", OUT)
print("scope", dict(Counter(r["scope"] for r in rows)), "severity", dict(Counter(r["gold_severity"] for r in rows)), "lang", dict(Counter(r["lang"] for r in rows)))
