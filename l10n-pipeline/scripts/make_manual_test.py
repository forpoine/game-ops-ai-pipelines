"""수작업 검수 시간 측정용 '시험지'를 만든다(정답 표시 없음, 순서 섞음).
out/manual_test.html : 사람이 푸는 시험지(스톱워치, 언어별 '문제 있음' 체크, 결과 복사)
out/manual_answer_key.json : 정답(사람이 풀기 전에는 열지 않는다)
같은 15건을 검수기에 돌린 시간도 함께 잰다. 실행: PYTHONIOENCODING=utf-8 python scripts/make_manual_test.py
"""
import html, json, random, time
from checker import ROOT, load_glossary, check_notice
import plant_errors as pe

import sys
if (ROOT / "out" / "manual_test.html").exists() and "--force" not in sys.argv:
    sys.exit("out/manual_test.html이 이미 있음. 사용자에게 보낸 시험지와 정답이 어긋나므로 덮어쓰지 않음(--force로만).")
G = load_glossary()
rnd = random.Random(11)
items = []
for n in pe.CLEAN:
    items.append({"notice": n, "planted": None})
for desc, kind, lg, nid, fn in pe.PLANTS:
    n = pe.get(nid); fn(n)
    items.append({"notice": n, "planted": {"kind": kind, "lang": lg, "desc": desc}})
rnd.shuffle(items)

# 검수기 소요(같은 15건)
t = time.perf_counter()
hits = 0
for it in items:
    n = it["notice"]
    iss = check_notice(n, G, pe.limits_for(n))
    it["checker"] = sorted({f"{x['lang']}:{x['kind']}" for x in iss})
ms = (time.perf_counter() - t) * 1000

key = {"checker_ms_for_15": round(ms, 2), "items": []}
rows = []
terms = sorted({t for it in items for t in it["notice"]["terms"]})
gl = "".join(f"<tr><td>{html.escape(G[t]['en'])}</td><td>{html.escape(G[t]['ko'])}</td><td>{html.escape(G[t]['ja'])}</td><td>{html.escape(G[t]['es'])}</td></tr>" for t in terms)
for i, it in enumerate(items, 1):
    n = it["notice"]
    key["items"].append({"no": i, "planted": it["planted"], "checker_flags": it["checker"]})
    lim = pe.limits_for(n)
    rows.append(
        f"<div class=n><b>문장 {i}</b> <small>(한도: ja {lim['ja']}자, es {lim['es']}자)</small>"
        f"<p class=en>EN 원문: {html.escape(n['en'])}</p>"
        + "".join(f"<label class=r><input type=checkbox data-n={i} data-l={lg}> <b>{lg.upper()}</b> {html.escape(n['tr'][lg])}</label>" for lg in ("ko", "ja", "es"))
        + "</div>")

page = f"""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>수작업 검수 시험지</title>
<style>body{{font:15px/1.6 system-ui,'Malgun Gothic',sans-serif;max-width:900px;margin:0 auto;padding:12px 16px;color:#222}}
#bar{{position:sticky;top:0;background:#fff;border-bottom:2px solid #333;padding:8px 0;z-index:2}}
#t{{font:700 28px monospace}}button{{font-size:16px;padding:6px 14px;margin-right:8px}}
.n{{border:1px solid #ccc;border-radius:8px;margin:12px 0;padding:8px 12px}}.en{{color:#555;margin:4px 0}}
.r{{display:block;padding:3px 4px}}.r:hover{{background:#f3f3f3}}table{{border-collapse:collapse}}td,th{{border:1px solid #ccc;padding:3px 8px}}
textarea{{width:100%;height:70px}}</style>
<div id=bar><span id=t>00:00.0</span> <button id=s>시작</button><button id=e>끝(멈춤)</button><button id=c>결과 만들기</button></div>
<h2>수작업 검수 시험지 (15문장)</h2>
<p><b>할 일</b>: 아래 용어표와 영어 원문을 기준으로, 각 번역 줄에서 <b>용어 표기, 숫자·날짜·시각, 확률 합계 100%, 비었거나 다른 언어가 들어감, 글자 수 한도 초과, [[T1]] 같은 자리표시자 잔존</b>을 찾고 문제가 있는 줄에 체크하세요. 일본어는 글자를 용어표와 대조하는 정도만 합니다(뜻 검증 아님). 한 문장에 문제가 없을 수도, 여러 개일 수도 있습니다. 번역의 자연스러움은 보지 않습니다.</p>
<p>순서: 시작을 누르고 → 끝까지 검수 → 끝(멈춤) → 결과 만들기 → 시간과 아래 결과 글을 Claude에게 붙여 주세요. 중간에 멈추지 말고, 검색·도구 없이 눈으로만.</p>
<h3>용어표</h3><table><tr><th>EN</th><th>KO</th><th>JA</th><th>ES</th></tr>{gl}</table>
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
(ROOT / "out").mkdir(exist_ok=True)
(ROOT / "out" / "manual_test.html").write_text(page, encoding="utf-8")
(ROOT / "out" / "manual_answer_key.json").write_text(json.dumps(key, ensure_ascii=False, indent=1), encoding="utf-8")
print("written out/manual_test.html (정답은 out/manual_answer_key.json, 열지 말 것)")
print("검수기 15건:", round(ms, 2), "ms")
