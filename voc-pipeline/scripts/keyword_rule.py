"""키워드 상향 규칙(01의 2번 규칙 후보)을 AI 예측 위에 얹어 효과를 잰다. 합성 데이터. LM Studio 불필요.
규칙: 글에 키워드가 있으면 심각도를 **최소 S2로 올린다**(내리지 않음). 키워드(01): 결제, 환불, 사라짐, 접속 불가, 소멸, 확률 조작.
사용: python scripts/keyword_rule.py <정답파일명> <pred_tag> [pred_tag...]    예: keyword_rule.py syn_voc_gold_v3.csv gemma_cap2 gptoss_cap2
변형: ko = 한국어 키워드만(01 원문), ko+en = 영어 대응어(payment, refund, disappear, can't log, rigged 등)를 더함.
출력: 규칙 전후 심각도 정확도, 규칙이 바꾼 행 중 도움(오답→정답)·해침(정답→오답)·무관 건수."""
import csv, sys, re, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
KO = ["결제", "환불", "사라", "접속 불가", "접속이 안", "소멸", "확률 조작"]
EN = ["payment", "paid", "refund", "disappear", "can't log", "cannot log", "unable to log", "rigged"]
ORDER = {"S1": 1, "S2": 2, "S3": 3, "S4": 4}
def hit(text, kws): t = text.lower(); return any(k in t for k in kws)
gold_file = sys.argv[1]; tags = sys.argv[2:]
gold = {r["id"]: r for r in csv.DictReader(open(ROOT/"data"/gold_file, encoding="utf-8-sig"))}
for tag in tags:
    P = list(csv.DictReader(open(ROOT/"data"/f"pred_{tag}.csv", encoding="utf-8-sig")))
    base = sum(r["pred_severity"] == gold[r["id"]]["gold_severity"] for r in P)
    print(f"== {tag} (정답 {gold_file}) 규칙 없음: 심각도 {base}/{len(P)}")
    for name, kws in (("ko", KO), ("ko+en", KO + EN)):
        helped = hurt = same = changed = 0; ok = 0
        for r in P:
            g = gold[r["id"]]["gold_severity"]; p = r["pred_severity"]; q = p
            if hit(gold[r["id"]]["text"], kws) and p in ORDER and ORDER[p] > 2: q = "S2"
            if q != p:
                changed += 1
                if q == g: helped += 1
                elif p == g: hurt += 1
                else: same += 1
            ok += q == g
        print(f"   규칙 {name}: 심각도 {ok}/{len(P)} ({ok-base:+d}), 규칙이 바꾼 행 {changed}건 = 도움 {helped} / 해침 {hurt} / 무관(어차피 오답) {same}")
