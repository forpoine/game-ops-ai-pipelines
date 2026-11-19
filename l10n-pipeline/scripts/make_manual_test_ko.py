"""수작업 검수 시험지 2차: 영어 원문 vs 한국어(검수자가 둘 다 읽는 언어).
1차 시험지(out/manual_test.html)는 오류를 스페인어·일본어에만 심어 검수자가 읽지 못하는 언어를 재는 셈이었다.
이번에는 한국어 칸에만 오류 10개를 심고 EN·KO만 보여 준다. 검수기도 ko 결과만 센다(같은 조건).
out/manual_test_ko.html : 시험지 / out/manual_answer_key_ko.json : 정답(풀기 전에 열지 않는다)
실행: PYTHONIOENCODING=utf-8 python scripts/make_manual_test_ko.py
채점: KEY_PATH=out/manual_answer_key_ko.json python scripts/score_manual.py "<결과 글>"
"""
import html, json, random, sys, time
from checker import ROOT, load_glossary, check_notice
import plant_errors as pe

OUT = ROOT / "out" / "manual_test_ko.html"
if OUT.exists() and "--force" not in sys.argv:
    sys.exit("out/manual_test_ko.html이 이미 있음. 정답과 어긋나므로 덮어쓰지 않음(--force로만).")

G = load_glossary()
KO_LIMIT = pe.limits_for(pe.CLEAN[0])["ko"]


def sub(n, a, b):
    pe.sub(n, "ko", a, b)


# (설명, 기대 종류, 공지 id 접두, 변형). 모두 ko 칸.
PLANTS = [
    ("용어: 그레이트회복약 -> 메가포션(영어 직역)", "term", "N1", lambda n: sub(n, "그레이트회복약", "메가포션")),
    ("용어: 하이퍼볼 -> 울트라볼(영어 직역)", "term", "N3", lambda n: sub(n, "하이퍼볼", "울트라볼")),
    ("용어: 기력의덩어리 -> 기력의조각(다른 아이템)", "term", "N4", lambda n: sub(n, "기력의덩어리", "기력의조각")),
    ("숫자: 점검 날짜 12-03 -> 12-30", "number", "N1", lambda n: sub(n, "2026-12-03", "2026-12-30")),
    ("숫자: 출현 시각 20:00 -> 21:00", "number", "N3", lambda n: sub(n, "20:00", "21:00")),
    ("숫자: 보상 만료 14일 -> 7일", "number", "N4", lambda n: sub(n, "14일", "7일")),
    ("확률: 갑옥 30% -> 20%(합 90%)", "prob", "N5", lambda n: sub(n, "30%", "20%")),
    ("자리표시자 잔존: 용옥 -> [[T1]]", "leftover", "N5", lambda n: sub(n, "용옥", "[[T1]]")),
    ("영어 잔존: 저녁 호수 -> Evening Lake", "english", "N3", lambda n: sub(n, "저녁 호수", "Evening Lake")),
    ("글자 넘침(ko 한도 초과)", "overflow", "N2", lambda n: n["tr"].__setitem__(
        "ko", n["tr"]["ko"] + " 자세한 내용은 게임 내 공지사항을 확인해 주시기 바랍니다." * (KO_LIMIT // 30 + 1))),
]

rnd = random.Random(23)
items = [{"notice": n, "planted": None} for n in pe.CLEAN]
for desc, kind, nid, fn in PLANTS:
    n = pe.get(nid); fn(n)
    items.append({"notice": n, "planted": {"kind": kind, "lang": "ko", "desc": desc}})
rnd.shuffle(items)

t = time.perf_counter()
for it in items:
    n = it["notice"]
    iss = check_notice(n, G, pe.limits_for(n))
    it["checker"] = sorted({f"{x['lang']}:{x['kind']}" for x in iss if x["lang"] == "ko"})
ms = (time.perf_counter() - t) * 1000

key = {"checker_ms_for_15": round(ms, 2), "langs": ["ko"], "items": []}
terms = sorted({t for it in items for t in it["notice"]["terms"]})
gl = "".join(f"<tr><td>{html.escape(G[t]['en'])}</td><td>{html.escape(G[t]['ko'])}</td></tr>" for t in terms)
rows = []
for i, it in enumerate(items, 1):
    n = it["notice"]
    key["items"].append({"no": i, "planted": it["planted"], "checker_flags": it["checker"]})
    rows.append(
        f"<div class=n><b>문장 {i}</b>"
        f"<p class=en>EN 원문: {html.escape(n['en'])}</p>"
        f"<label class=r><input type=checkbox data-n={i} data-l=ko> <b>KO</b> {html.escape(n['tr']['ko'])}</label></div>")

page = f"""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>수작업 검수 시험지 2 (영어·한국어)</title>
<style>body{{font:15px/1.6 system-ui,'Malgun Gothic',sans-serif;max-width:900px;margin:0 auto;padding:12px 16px;color:#222}}
#bar{{position:sticky;top:0;background:#fff;border-bottom:2px solid #333;padding:8px 0;z-index:2}}
#t{{font:700 28px monospace}}button{{font-size:16px;padding:6px 14px;margin-right:8px}}
.n{{border:1px solid #ccc;border-radius:8px;margin:12px 0;padding:8px 12px}}.en{{color:#555;margin:4px 0}}
.r{{display:block;padding:3px 4px}}.r:hover{{background:#f3f3f3}}table{{border-collapse:collapse}}td,th{{border:1px solid #ccc;padding:3px 8px}}
textarea{{width:100%;height:70px}}</style>
<div id=bar><span id=t>00:00.0</span> <button id=s>시작</button><button id=e>끝(멈춤)</button><button id=c>결과 만들기</button></div>
<h2>수작업 검수 시험지 2: 영어 원문 vs 한국어 (15문장)</h2>
<p><b>할 일</b>: 용어표와 영어 원문을 기준으로 한국어 줄에서 <b>용어 표기(용어표와 다름), 숫자·날짜·시각, 확률 합계 100%, 번역 안 된 영어, [[T1]] 같은 자리표시자, 글자 수 한도({KO_LIMIT}자) 초과</b>를 찾고 문제가 있으면 체크하세요. 한 문장에 문제가 없을 수도 있습니다. 문장의 자연스러움은 보지 않습니다.</p>
<p>순서: 시작 → 끝까지 검수 → 끝(멈춤) → 결과 만들기 → 결과 글을 Claude에게 붙여 주세요. 중간에 멈추지 말고, 검색·도구 없이 눈으로만.</p>
<h3>용어표</h3><table><tr><th>EN</th><th>KO</th></tr>{gl}</table>
{''.join(rows)}
<h3>결과</h3><textarea id=o readonly placeholder="결과 만들기를 누르면 여기에 나옵니다"></textarea>
<script>
let st=0,tm=null,el=0;const T=document.getElementById('t');
function fmt(ms){{const s=ms/1000;return String(Math.floor(s/60)).padStart(2,'0')+':'+(s%60).toFixed(1).padStart(4,'0')}}
document.getElementById('s').onclick=()=>{{if(tm)return;st=performance.now();tm=setInterval(()=>{{el=performance.now()-st;T.textContent=fmt(el)}},100)}};
document.getElementById('e').onclick=()=>{{if(tm){{clearInterval(tm);tm=null;el=performance.now()-st;T.textContent=fmt(el)}}}};
document.getElementById('c').onclick=()=>{{const f=[...document.querySelectorAll('input:checked')].map(i=>'문장'+i.dataset.n+' '+i.dataset.l);
document.getElementById('o').value='시간 '+fmt(el)+' ('+Math.round(el/1000)+'초)\\n체크: '+(f.join(', ')||'없음')}};
</script>"""
OUT.write_text(page, encoding="utf-8")
(ROOT / "out" / "manual_answer_key_ko.json").write_text(json.dumps(key, ensure_ascii=False, indent=1), encoding="utf-8")
hit = sum(1 for it in items if it["planted"] and it["checker"])
fp = sum(1 for it in items if not it["planted"] and it["checker"])
kind_ok = sum(1 for it in items if it["planted"] and f"ko:{it['planted']['kind']}" in it["checker"])
print(f"written {OUT.name} / 검수기 ko: 검출 {hit}/10 (종류 일치 {kind_ok}/10), 정상 오탐 {fp}, {ms:.2f} ms")
