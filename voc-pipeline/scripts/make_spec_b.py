"""Set B 지시표(80건, 급증 없음, 말투·길이 변수 추가). Set A와 시드만 다르다. 전부 합성. 서비스명은 {SERVICE} 자리표시자.
출력: data/syn_voc_b_spec.csv  (id, ts, lang, gold_category, gold_severity, gold_sentiment,
gold_cluster, ambiguous, secondary_category, seed)
설계 값이며 측정값이 아니다. random seed 고정."""
import csv, random, datetime as dt, pathlib

random.seed(11)
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "syn_voc_b_spec.csv"

# (category, seed text, cluster, severity choices, sentiment choices)
SEEDS = {
 "BUG": [
  ("전투 중 앱이 갑자기 튕김", "crash_battle", ["S2","S3"]),
  ("로딩 화면에서 멈춰 진행 불가", "loading_stuck", ["S2"]),
  ("로그인이 안 됨, 접속 불가", "login_fail", ["S1","S2"]),
  ("결제 후 재화가 들어오지 않음", "payment_missing", ["S1","S2"]),
  ("UI 글자가 겹쳐 보임", "ui_overlap", ["S3","S4"]),
  ("퀘스트 완료 표시가 안 되어 다음 진행 불가", "quest_block", ["S2","S3"]),
  ("저장 데이터가 사라짐", "data_loss", ["S1","S2"]),
 ],
 "BAL": [
  ("특정 캐릭터가 너무 강함", "bal_strong_char", ["S3"]),
  ("보스 난이도가 지나치게 높음", "bal_boss_hard", ["S3"]),
  ("매칭에서 실력 차가 큼", "bal_matching", ["S3"]),
  ("패치 후 무기 성능 하향 불만", "bal_nerf", ["S3","S4"]),
  ("초반 난이도가 너무 쉬움", "bal_easy", ["S4"]),
 ],
 "MON": [
  ("확률형 상품 확률이 낮게 느껴짐", "mon_gacha_rate", ["S2","S3"]),
  ("패키지 가격 대비 구성 불만", "mon_package", ["S3","S4"]),
  ("실수 결제 환불 요청", "mon_refund", ["S2","S3"]),
  ("확률 조작 의혹 제기", "mon_rate_suspect", ["S2"]),
  ("월정액 혜택 부족", "mon_sub", ["S3","S4"]),
 ],
 "OPS": [
  ("이벤트 보상이 누락됨", "ops_reward_missing", ["S2","S3"]),
  ("업데이트 노트와 실제 내용 불일치", "ops_note_mismatch", ["S3"]),
  ("보상 지급 기준 문의", "ops_reward_rule", ["S4","S3"]),
  ("이벤트 기간 안내 불명확", "ops_event_period", ["S3"]),
 ],
 "COM": [
  ("매크로·핵 의심 유저 신고", "com_cheat", ["S2","S3"]),
  ("채팅 욕설 신고", "com_abuse", ["S3"]),
  ("제재가 억울하다는 항의", "com_sanction", ["S3"]),
  ("거래 사기 피해 제보", "com_scam", ["S2"]),
 ],
 "ETC": [
  ("새 콘텐츠 제안", "etc_suggest", ["S4"]),
  ("업데이트 칭찬", "etc_praise", ["S4"]),
  ("계정 이전 방법 단순 문의", "etc_inquiry", ["S4"]),
 ],
}
COUNTS = {"BUG": 22, "BAL": 16, "MON": 16, "OPS": 8, "COM": 9, "ETC": 9}  # 합계 80
SENT = {"BUG": ["neg","neg","neu"], "BAL": ["neg","neg","neu"], "MON": ["neg","neg","neu"],
        "OPS": ["neg","neu"], "COM": ["neg","neu"], "ETC": ["pos","neu","pos"]}
SECOND = {"BUG": "MON", "MON": "BAL", "OPS": "MON", "COM": "BUG", "BAL": "MON"}
LANGS = ["ko"] * 67 + ["en"] * 17 + ["mixed"] * 16
STYLES = ["짧은 반말", "정중한 존댓말", "감정이 격한 말투", "건조한 보고체", "푸념하듯 늘어지는 말투"]
LENS = ["1문장", "1~2문장", "2~3문장"]
START = dt.datetime(2026, 4, 6, 0, 0)  # 합성 날짜(실제 사건 아님)
rows = []
for cat, n in COUNTS.items():
    for _ in range(n):
        seed, cl, sev = random.choice(SEEDS[cat])
        rows.append(dict(gold_category=cat, seed=seed, gold_cluster=cl, gold_severity=random.choice(sev),
                         gold_sentiment=random.choice(SENT[cat]), day=random.randint(0, 6)))
random.shuffle(rows)
amb_idx = [i for i, r in enumerate(rows) if r["gold_category"] in SECOND]
for i in random.sample(amb_idx, 11):
    rows[i]["ambiguous"] = True
    rows[i]["secondary"] = SECOND[rows[i]["gold_category"]]
for r in rows:
    r["lang"] = random.choice(LANGS); r["style"] = random.choice(STYLES); r["length"] = random.choice(LENS)
    r["ts"] = (START + dt.timedelta(days=r["day"], hours=random.randint(0, 23), minutes=random.randint(0, 59))).strftime("%Y-%m-%d %H:%M")
rows.sort(key=lambda r: r["ts"])
cols = ["id","ts","lang","style","length","gold_category","gold_severity","gold_sentiment","gold_cluster","ambiguous","secondary_category","seed"]
OUT.parent.mkdir(exist_ok=True)
with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
    for i, r in enumerate(rows, 1):
        w.writerow(dict(id=f"SYNB-{i:04d}", ts=r["ts"], lang=r["lang"], style=r["style"], length=r["length"],
            gold_category=r["gold_category"], gold_severity=r["gold_severity"], gold_sentiment=r["gold_sentiment"],
            gold_cluster=r["gold_cluster"], ambiguous=str(bool(r.get("ambiguous"))).lower(),
            secondary_category=r.get("secondary",""), seed=r["seed"]))
print(len(rows), "rows ->", OUT)
