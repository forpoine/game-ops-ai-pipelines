"""spec의 각 행에 맞는 합성 VOC 본문을 LM Studio(gemma)로 생성. 전부 합성.
사용: python scripts/generate_voc.py [N]   (N이면 앞 N건만 시험)
출력: data/syn_voc_generated.csv (label_status=generated, is_synthetic=true)"""
import csv, sys, json, pathlib, urllib.request, re
ROOT = pathlib.Path(__file__).resolve().parent.parent
SPEC, OUT = ROOT/"data"/"syn_voc_spec.csv", ROOT/"data"/"syn_voc_generated.csv"
MODEL = "google/gemma-4-12b-qat"
CAT = {"BUG":"버그·오류","BAL":"밸런스","MON":"과금·확률","OPS":"운영·공지","COM":"커뮤니티·불건전 이용","ETC":"기타(제안·칭찬·문의)"}
SEV = {"S1":"매우 긴급(다수 영향)","S2":"높음","S3":"보통","S4":"낮음"}
SENT = {"pos":"긍정","neu":"중립(차분한 어조)","neg":"부정"}
LANG = {"ko":"한국어","en":"영어","mixed":"한국어와 영어가 섞인 말투"}
def prompt(r):
    p = (f"가상의 모바일 게임 {{SERVICE}}에 유저가 남긴 의견 한 건을 써라.\n"
         f"- 주제: {r['seed']}\n- 언어: {LANG[r['lang']]}\n- 어조: {SENT[r['gold_sentiment']]}\n"
         f"- 문제의 급한 정도(글에 드러나게, 직접 단계명은 쓰지 말 것): {SEV[r['gold_severity']]}\n"
         "- 1~3문장, 실제 유저처럼 구어체, 이모티콘·오타 약간 허용.\n"
         "- 실제 게임 이름·캐릭터·실명·계정 ID 금지. 게임은 '이 게임'이나 {SERVICE}로만 부른다.\n")
    if r["ambiguous"] == "true":
        p += f"- 이 글은 '{CAT[r['gold_category']]}' 문제가 핵심이지만 '{CAT[r['secondary_category']]}' 이야기도 살짝 섞어 판단이 갈리게 쓴다.\n"
    if r["gold_cluster"] == "surge_notice_time_error":
        p += "- 상황: 점검 종료 시각을 공지가 잘못 알려서 그 시각에 기다렸는데 접속이 안 됐다. 시각 숫자는 구체적으로 한 번 언급(예: 공지 오후 3시, 실제 오후 5시).\n"
    p += "출력은 유저 글 본문만, 따옴표·설명 없이."
    return p
def ask(p):
    body = json.dumps({"model":MODEL,"messages":[{"role":"user","content":p}],"max_tokens":3000,"temperature":0.9}).encode()
    req = urllib.request.Request("http://localhost:1234/v1/chat/completions", body, {"Content-Type":"application/json"})
    return json.load(urllib.request.urlopen(req, timeout=300))["choices"][0]["message"]["content"].strip().strip('"')
rows = list(csv.DictReader(open(SPEC, encoding="utf-8-sig")))
n = int(sys.argv[1]) if len(sys.argv) > 1 else len(rows)
cols = ["id","ts","lang","text","gold_category","gold_severity","gold_sentiment","gold_cluster","ambiguous","label_status","is_synthetic"]
with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
    for r in rows[:n]:
        t = re.sub(r"\s+", " ", ask(prompt(r)))
        w.writerow({**{k:r[k] for k in cols if k in r}, "text":t, "label_status":"generated", "is_synthetic":"true"})
        f.flush(); print(r["id"], r["gold_category"], r["gold_severity"], "|", t[:70], flush=True)
