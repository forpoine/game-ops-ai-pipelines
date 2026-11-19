"""사람 승인용 HTML 리포트. 검수기 결과를 공지별 표로 보여주고, 이슈가 있으면 빨간 표시.
승인 체크박스는 브라우저에서만 동작(저장 없음, 화면 확인용).
사용: from report import write_report; write_report(notices, glossary, limits, "out/report.html")
실행(데모): PYTHONIOENCODING=utf-8 python scripts/report.py
"""
import html, sys
from pathlib import Path
from checker import check_notice, load_glossary, LANGS

LANG_NAME = {"en": "EN 원문", "ko": "KO", "ja": "JA (사람 검증 안 함)", "es": "ES"}
CSS = """body{font:15px/1.6 system-ui,'Malgun Gothic',sans-serif;margin:24px auto;max-width:880px;padding:0 16px;color:#222}
.n{border:1px solid #ccc;border-radius:8px;margin:16px 0;padding:12px 16px}.n.bad{border-color:#c0392b;background:#fdf3f2}
.n.ok{border-color:#2e8b57}table{border-collapse:collapse;width:100%}td{padding:4px 8px;vertical-align:top;border-top:1px solid #eee}
td:first-child{width:130px;color:#666;white-space:nowrap}.i{color:#c0392b;font-size:13px}.tag{font-weight:600}
"""


def write_report(notices, glossary, limits, out_path):
    parts, total_bad = [], 0
    for n in notices:
        iss = check_notice(n, glossary, limits(n) if callable(limits) else limits)
        total_bad += bool(iss)
        rows = [f"<tr><td>{LANG_NAME['en']}</td><td>{html.escape(n['en'])}</td></tr>"]
        for lg in LANGS:
            mine = [x for x in iss if x["lang"] == lg]
            note = "".join(f"<div class=i>[{x['kind']}] {html.escape(x['detail'])}</div>" for x in mine)
            rows.append(f"<tr><td>{LANG_NAME[lg]}</td><td>{html.escape(n['tr'].get(lg, ''))}{note}</td></tr>")
        for x in (i for i in iss if i["lang"] == "en"):
            rows.append(f"<tr><td>원문</td><td class=i>[{x['kind']}] {html.escape(x['detail'])}</td></tr>")
        status = f"이슈 {len(iss)}건" if iss else "이슈 없음"
        parts.append(f"<div class='n {'bad' if iss else 'ok'}'><div class=tag>{html.escape(str(n['id']))} · {status}"
                     f" <label style='float:right'><input type=checkbox> 사람 승인</label></div><table>{''.join(rows)}</table></div>")
    head = f"<h1>번역 검수 리포트</h1><p>공지 {len(notices)}건 중 이슈가 있는 것 {total_bad}건. 규칙 검사 결과이며 최종 승인은 사람이 한다.</p>"
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(f"<!doctype html><meta charset=utf-8><title>검수 리포트</title><style>{CSS}</style>{head}{''.join(parts)}", encoding="utf-8")
    return total_bad


if __name__ == "__main__":
    import test_checker as t
    cases = [dict(c) for c in t.CLEAN] + [dict(n, id=f"심은오류: {d}") for d, _, n in t.planted()]
    bad = write_report(cases, load_glossary(), t.LIMITS, Path(__file__).resolve().parent.parent / "out" / "report_demo.html")
    print("written out/report_demo.html, 이슈 있는 공지", bad, "/", len(cases))
