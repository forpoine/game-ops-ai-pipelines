"""합성 VOC를 LM Studio 모델로 분류(카테고리·심각도·감성). 전부 합성 데이터.
사용: python scripts/classify.py <model_id> <tag> [N]   예: classify.py google/gemma-4-12b-qat gemma 5
입력 data/syn_voc_gold.csv (정답 열은 모델에 보내지 않음), 출력 data/pred_<tag>.csv
실패 처리(2026-11-18 사용자 확정): 형식이 깨진 응답은 같은 요청으로 한 번 다시 보내고, 그래도 실패하면 needs_review=1(사람 검수).
VOC_RETRY=0이면 재시도하지 않는다(이 코드 추가 전 측정과 같은 동작)."""
import csv, sys, json, pathlib, urllib.request, re, time
ROOT = pathlib.Path(__file__).resolve().parent.parent
import os
GOLD = ROOT/"data"/(os.environ.get("VOC_GOLD") or ("syn_voc_b_gold.csv" if os.environ.get("VOC_SET")=="b" else "syn_voc_gold.csv"))
model, tag = sys.argv[1], sys.argv[2]
OUT = ROOT/"data"/f"pred_{tag}.csv"
SYSTEM = """너는 게임 서비스 운영팀의 VOC 분류기다. 유저 글 한 건을 읽고 JSON 한 줄만 출력한다.
카테고리(핵심 하나): BUG 버그·오류(튕김, 접속 불가, 진행 불가, 결제 오류, 데이터 손실) / BAL 밸런스(캐릭터 강약, 난이도, 매칭) / MON 과금·확률(가격, 확률 의혹, 환불 요청, 패키지 불만) / OPS 운영·공지(점검 시간, 공지 오류·오해, 이벤트 보상 누락) / COM 커뮤니티·불건전 이용(핵·매크로 의심, 비매너, 사기, 제재 불만) / ETC 기타(제안, 칭찬, 단순 문의)
심각도: S1 다수 영향 접속 불가·결제 오류·재화 손실, 공지 오기 / S2 핵심 기능 오작동, 진행 불가, 확률·보상 신뢰 훼손 의혹, 심각한 불건전 이용 / S3 우회 가능한 불편, 밸런스·난이도 불만, 일반 제재 불만 / S4 제안, 칭찬, 단순 문의
감성: pos / neu / neg (어조만. 심각도와 독립)
경계 규칙: 섞이면 유저가 해결을 바라는 것 기준. 공지 때문에 생긴 항의는 OPS. 제재 불만은 COM.
출력 형식: {"category":"BUG","severity":"S2","sentiment":"neg"}"""
if os.environ.get("VOC_PROMPT") in ("cap", "cap2"):
    _a=SYSTEM.index("심각도:"); _b=SYSTEM.index(" S3 ")
    SYSTEM=SYSTEM[:_a]+"심각도(글 한 건만 보므로 규모를 알 수 없다. S1은 쓰지 말고 S2 이하로만 판단): S2 핵심 기능 오작동, 진행 불가, 접속 불가·결제 오류·재화 손실·공지 오기, 확률·보상 신뢰 훼손 의혹, 심각한 불건전 이용 /"+SYSTEM[_b:]
if os.environ.get("VOC_PROMPT")=="cap2":
    # cap + 4단계 오류 사례에서 도출한 심각도 경계 규칙(01의 1-2 아래, 2026-11-18). 같은 글에서 도출한 규칙이므로 이 글들에서의 점수는 낙관적이다.
    SYSTEM=SYSTEM.replace("\n감성:", "\n심각도 경계: 너무 어려워 진행이 막히는 불만은 S3, '너무 쉽다'나 구성이 아쉽다 같은 취향성 의견은 S4. 구매 전에 알 수 있던 패키지 구성·월정액 혜택이 아쉽다는 불만은 S4(표시나 공지와 다르다는 주장은 S2). 이벤트 보상을 못 받음, 진행 손실을 동반한 튕김, 퀘스트 완료 표시 안 됨은 S2. 업데이트 노트와 실제가 다르다는 '기대와 다름'은 S3.\n감성:")
def ask(text):
    body = json.dumps({"model":model,"messages":[{"role":"system","content":SYSTEM},{"role":"user","content":text}],
                       "max_tokens":int(os.environ.get("VOC_MAX_TOKENS","4000")),"temperature":0}).encode()
    req = urllib.request.Request("http://localhost:1234/v1/chat/completions", body, {"Content-Type":"application/json"})
    return json.load(urllib.request.urlopen(req, timeout=600))["choices"][0]["message"]["content"]
RETRY = int(os.environ.get("VOC_RETRY", "1"))
VALID = {"category":{"BUG","BAL","MON","OPS","COM","ETC"},"severity":{"S1","S2","S3","S4"},"sentiment":{"pos","neu","neg"}}
def parse(raw):
    m = re.search(r"\{.*?\}", raw or "", re.S)
    try: d = json.loads(m.group(0))
    except Exception: d = {}
    return d, all(d.get(k) in v for k, v in VALID.items())
rows = list(csv.DictReader(open(GOLD, encoding="utf-8-sig")))
n = int(sys.argv[3]) if len(sys.argv) > 3 else len(rows)
with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["id","pred_category","pred_severity","pred_sentiment","sec","raw","tries","needs_review"]); w.writeheader()
    for r in rows[:n]:
        t0 = time.time(); tries = 0
        while True:
            tries += 1; raw = ask(r["text"]); d, ok = parse(raw)
            if ok or tries > RETRY: break
        sec = round(time.time()-t0, 1)
        w.writerow({"id":r["id"],"pred_category":d.get("category",""),"pred_severity":d.get("severity",""),
                    "pred_sentiment":d.get("sentiment",""),"sec":sec,"raw":re.sub(r"\s+"," ",raw or "")[:200],
                    "tries":tries,"needs_review":0 if ok else 1})
        f.flush(); print(r["id"], d, sec, flush=True)
