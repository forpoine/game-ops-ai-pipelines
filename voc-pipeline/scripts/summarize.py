"""6단계: 담당 조직 전달용 요약 초안. 합성 데이터. LM Studio에 Gemma가 로드돼 있어야 한다.
역할 분담(02 6단계 설계, Claude 초안): 숫자·시각·건수·담당 조직·급증 규칙 충족 여부는 **규칙이 계산해 머리말로 붙이고**, AI(Gemma)는 본문 세 문장(무슨 일, 유저 반응, 요청된 조치)만 쓴다.
AI 본문에 글에 없는 숫자가 들어가면 규칙이 표시한다(근거 확인). 사람이 고친 내용은 사용자가 나중에 `사용자 수정` 칸에 적는다.
대상(Set A): 정답 주제 6개(급증·결제 누락·매칭 밸런스·확률·채팅 욕설·제안)와 **클러스터링 결과의 섞인 큰 클러스터 1개**(나쁜 클러스터에 요약을 붙이면 어떻게 되는지 보려고).
사용: python scripts/summarize.py    결과 data/summary_drafts.csv, data/summary_drafts.md
머리말만 다시 계산: VOC_REUSE=1 python scripts/summarize.py  (LLM 호출 없이 기존 csv의 AI 본문과 사용자 수정 칸을 그대로 쓰고 머리말·근거 확인만 새로 계산)
주제 혼재 규칙(2026-11-18 사용자 결정): 머리말에 카테고리 분포를 적고, 다수 카테고리 비율이 절반 미만이면 담당 조직을 하나로 찍지 않고 "주제 혼재, 사람이 재분배"로 표시."""
import csv, sys, re, os, json, time, urllib.request, pathlib, datetime as dt, collections as C
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/"scripts")); import detect
MODEL = "google/gemma-4-12b-qat"
ORG = {"BUG": "개발·QA", "BAL": "기획", "MON": "사업·기획·고객센터", "OPS": "서비스 운영·커뮤니케이션", "COM": "서비스 운영·제재 담당", "ETC": "서비스 운영"}
TOPICS = ["surge_notice_time_error", "payment_missing", "bal_matching", "mon_gacha_rate", "com_abuse", "etc_suggest"]
SYSTEM = """너는 게임 서비스 운영팀에서 유저 의견(VOC)을 담당 조직에 전달하는 담당자다. 아래 유저 글 묶음을 {org}에 보낼 요약으로 쓴다.
규칙: 글에 있는 내용만 쓴다. 숫자, 시각, 건수는 쓰지 않는다(시스템이 따로 붙인다). 원인을 추측하거나 단정하지 않는다. {SERVICE}는 그대로 쓴다. 한국어로 쓴다.
형식(세 줄, 번호와 제목 붙여서):
1) 무슨 일인가: 한 문장
2) 유저 반응: 한 문장
3) 요청된 조치: 한 문장(글에 요청이 없으면 "명시적 요청 없음")"""
def ask(system, user):
    if os.environ.get("VOC_DRY"): return "1) 무슨 일인가: (시험용 문장, 숫자 99 포함)\n2) 유저 반응: 시험\n3) 요청된 조치: 명시적 요청 없음"   # LLM 없이 규칙 부분만 시험
    body = json.dumps({"model": MODEL, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                       "max_tokens": 4000, "temperature": 0}).encode()
    req = urllib.request.Request("http://localhost:1234/v1/chat/completions", body, {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=900))["choices"][0]["message"]["content"] or ""
rows = {r["id"]: r for r in detect.load("a")}
gold_v3 = {r["id"]: r for r in csv.DictReader(open(ROOT/"data"/"syn_voc_gold_v3.csv", encoding="utf-8-sig"))}
def read_pred(f): return {r["id"]: r for r in csv.DictReader(open(ROOT/"data"/f, encoding="utf-8-sig"))} if (ROOT/"data"/f).exists() else {}
pred = read_pred("pred_gemma_cap2.csv")
if len(pred) < len(rows): pred = read_pred("pred_gemma_cap.csv")   # cap2가 아직 안 끝났으면 옛 결과로 대신(머리말의 AI 분류 표시용)
groups = [(f"정답 주제 {t}", [i for i, r in rows.items() if r["gold_cluster"] == t]) for t in TOPICS]
cl = list(csv.DictReader(open(ROOT/"data"/"cluster_a.csv", encoding="utf-8-sig")))
by = C.defaultdict(list)
for r in cl: by[r["pred_cluster"]].append(r["id"])
big = max(by.items(), key=lambda x: len(x[1]))
groups.append((f"클러스터링 결과 클러스터 {big[0]}(가장 큼, 주제 섞임)", big[1]))
REUSE = {}
if os.environ.get("VOC_REUSE"):
    REUSE = {r["group"]: r for r in csv.DictReader(open(ROOT/"data"/"summary_drafts.csv", encoding="utf-8-sig"))}
out = []
for name, ids in groups:
    ids = sorted(ids, key=lambda i: rows[i]["t"]); ts = [rows[i]["t"] for i in ids]
    cats = C.Counter(pred[i]["pred_category"] for i in ids if pred[i]["pred_category"]); cat, cn = cats.most_common(1)[0]
    sevs = sorted(pred[i]["pred_severity"] for i in ids if pred[i]["pred_severity"])
    al = detect.alerts([(rows[i]["t"], "g", False) for i in ids], 5, 3)
    mixed = cn / len(ids) < 0.5
    dist = ", ".join(f"{c} {k}" for c, k in cats.most_common())
    owner = (f"주제 혼재(다수 비율 절반 미만), 담당 하나로 정하지 않음: 사람이 재분배({', '.join(f'{c}→{ORG[c]}' for c, _ in cats.most_common())})"
             if mixed else f"담당 {ORG[cat]}")
    header = (f"{len(ids)}건, {min(ts):%m-%d %H:%M}~{max(ts):%m-%d %H:%M}, AI 분류 카테고리 분포 [{dist}], 다수 {cat}({cn}/{len(ids)}), {owner}, "
              f"글 단위 심각도 AI 예측 {dict(C.Counter(sevs))}, 급증 규칙(3시간 5건) {'충족: 이슈 단위 S1 승격' if al else '미충족'}")
    user = "\n".join(f"{n+1}. {rows[i]['text'][:220]}" for n, i in enumerate(ids[:25]))
    org_for_prompt = "여러 담당 조직" if mixed else ORG[cat]
    if name in REUSE: body = REUSE[name]["ai_body"]
    else:
        body = ask(SYSTEM.replace("{org}", org_for_prompt), user)
        if not body.strip(): body = ask(SYSTEM.replace("{org}", org_for_prompt), user)
    src = " ".join(rows[i]["text"] for i in ids) + " " + header
    body_nums = re.findall(r"\d+", re.sub(r"^\s*\d\)", "", body, flags=re.M))   # 형식의 번호 "1)"은 제외
    extra = sorted({d for d in body_nums if d not in re.findall(r"\d+", src)})
    flags = f"본문 숫자 중 글에 없는 것: {extra}" if extra else "본문 숫자 근거 확인 통과(글에 없는 숫자 없음)"
    if not body.strip(): flags = "AI 본문 비어 있음(형식 실패)"
    out.append(dict(group=name, n=len(ids), header=header, ai_body=re.sub(r"[ \t]+", " ", body.strip()), rule_check=flags, user_edit=REUSE.get(name, {}).get("user_edit", "")))
    print(name, "->", flags, flush=True)
with open(ROOT/"data"/"summary_drafts.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
with open(ROOT/"data"/"summary_drafts.md", "w", encoding="utf-8") as f:
    f.write("# 담당 조직 전달용 요약 초안 (AI 본문 + 규칙 머리말). 전부 합성 데이터.\n머리말은 규칙이 계산, 본문은 Gemma가 작성. 사용자 수정은 사람이 검수한 본문(빈 칸은 수정 없음 또는 검수 전).\n\n")
    for o in out:
        edit = o["user_edit"].strip() or "(없음)"
        f.write(f"## {o['group']}\n- 머리말(규칙): {o['header']}\n- 근거 확인(규칙): {o['rule_check']}\n- AI 본문(초안):\n\n{o['ai_body']}\n\n- 사용자 수정:\n\n{edit}\n\n")
print("saved summary_drafts.csv / .md")
