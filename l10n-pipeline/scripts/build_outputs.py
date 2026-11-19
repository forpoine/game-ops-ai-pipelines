"""산출물 생성(LLM 없음): 모델별 승인용 리포트 3개 + 모델 비교 한 장(out/summary.html).
실행: PYTHONIOENCODING=utf-8 python scripts/build_outputs.py
"""
import html, json, re
from checker import ROOT, load_glossary, check_notice
from report import write_report

G = load_glossary()
MODELS = [("Gemma 12B", "google_gemma-4-12b-qat", "gemma"), ("gpt-oss 20B", "openai_gpt-oss-20b", "gptoss"), ("Qwen3 14B", "qwen3-14b", "qwen")]
# 공지 5종 번역 소요(초): gpt-oss/qwen은 로그 마지막 줄, Gemma는 실행 출력(204초, 로그 파일 없음)
GEMMA_SECS = 204


def limits_for(n):  # 글자 수 한도는 가정값(영어 길이 1.3배 등). Photoshop 수치가 나오면 교체.
    return {"ko": 400, "ja": int(len(n["tr"]["ko"]) * 1.3), "es": int(len(n["en"]) * 1.3)}


def secs(log):
    p = ROOT / "results" / f"log_{log}_notices.txt"
    if not p.exists():
        return None
    m = re.findall(r"(\d+)s\s*$", p.read_text(encoding="utf-8"), re.M)
    return int(m[-1]) if m else None


def rate(rows, lg):
    return sum(x["langs"][lg]["match"] for x in rows)


rows_base, rows_notice = [], []
for label, f, log in MODELS:
    notices = json.load(open(ROOT / "notices" / f"translated_{f}.json", encoding="utf-8"))
    bad = write_report(notices, G, limits_for, ROOT / "out" / f"report_{log}.html")
    iss = []
    for n in notices:  # 현재 검수기로 재검수
        iss += [f"{n['id'][:2]} {x['lang']}:{x['kind']}" for x in
                check_notice({"en": n["en"], "terms": n["terms"], "tr": n["tr"], "prob": n.get("prob")}, G, limits_for(n))]
    t = GEMMA_SECS if log == "gemma" else secs(log)
    rows_notice.append(f"<tr><td>{label}</td><td>{len(iss)}</td><td>{html.escape(', '.join(iss) or '없음')}</td><td>{t if t is not None else '?'}초</td><td><a href='report_{log}.html'>리포트</a></td></tr>")
    b = json.load(open(ROOT / "results" / f"{f}_baseline.json", encoding="utf-8"))
    p = json.load(open(ROOT / "results" / f"{f}_protected.json", encoding="utf-8"))
    rows_base.append(f"<tr><td>{label}</td><td>{rate(b,'ko')}/40</td><td>{rate(b,'ja')}/40</td><td>{rate(b,'es')}/40</td>"
                     f"<td>{rate(p,'ko')}/40, {rate(p,'ja')}/40, {rate(p,'es')}/40</td></tr>")

CSS = "body{font:15px/1.6 system-ui,'Malgun Gothic',sans-serif;max-width:900px;margin:24px auto;padding:0 16px;color:#222}table{border-collapse:collapse;margin:8px 0 20px}td,th{border:1px solid #ccc;padding:5px 10px;text-align:left}th{background:#f4f4f4}small{color:#666}"
page = f"""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>모델 비교 요약</title><style>{CSS}</style>
<h1>용어 보호 번역: 모델 비교 요약</h1>
<small>합성 데이터. 서비스는 가상, 용어는 몬스터헌터·포켓몬 텍스트 데이터만. 일본어는 사람이 검증하지 않음. 모든 수치는 이 프로젝트에서 잰 값.</small>
<h2>1. 용어집 없이 번역했을 때 공식 표기 일치 (40문장)</h2>
<table><tr><th>모델</th><th>한국어</th><th>일본어</th><th>스페인어</th><th>용어 보호 시 자리표시자 유지(ko, ja, es)</th></tr>{''.join(rows_base)}</table>
<small>문장은 시드 고정 템플릿 40개, 표본이 작아 소수점 차이는 의미 없음. 용어 보호의 40/40은 자리표시자 유지 여부이고 공식명은 코드가 넣는다. 오답 유형 분석은 results/baseline_분석.md.</small>
<h2>2. 공지 5종 번역(용어 보호, 일본어·스페인어) 검수 결과</h2>
<table><tr><th>모델</th><th>이슈 수</th><th>이슈</th><th>번역 소요</th><th>승인용 리포트</th></tr>{''.join(rows_notice)}</table>
<small>검수기: 용어, 숫자·날짜, 언어 누락, 글자 수 넘침, 확률 합 100%, 자리표시자 잔존. 글자 수 한도는 가정값. 소요 시간은 각 모델의 번역 호출 합(모델 로드 시간 제외, GPU 조건 다름).</small>
"""
(ROOT / "out" / "summary.html").write_text(page, encoding="utf-8")
print("written out/summary.html + report_gemma/gptoss/qwen.html")
