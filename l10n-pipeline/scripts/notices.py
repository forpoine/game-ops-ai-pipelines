"""공지 원문(notices/notices_src.json)의 {T:id}를 언어별 공식명으로 치환하고,
영어 원문과 한국어 원문의 숫자·확률이 서로 맞는지 검수기로 확인한다(LLM 없음).
몬헌 용어의 ko 칸이 비어 있으면 영어명을 그대로 두고 [미기입]으로 표시한다.
실행: PYTHONIOENCODING=utf-8 python scripts/notices.py
"""
import json, re
from pathlib import Path
from checker import ROOT, load_glossary, check_notice

TAG = re.compile(r"\{T:([^}]+)\}")


def render(text, glossary, lang):
    def sub(m):
        t = glossary[m.group(1)]
        v = t.get(lang, "")
        return v if v else f"{t['en']}[미기입]"
    return TAG.sub(sub, text)


def load_notices():
    return json.loads((ROOT / "notices" / "notices_src.json").read_text(encoding="utf-8"))


def main():
    g = load_glossary()
    for n in load_notices():
        for t in n["terms"]:
            assert t in g, f"{n['id']}: 용어집에 없음 {t}"
        en = render(n["en"], g, "en")
        ko = render(n["ko"], g, "ko")
        # 영어를 원문, 한국어를 번역으로 놓고 숫자/확률 대조. 용어는 ko 칸이 있는 것만 검사됨.
        iss = check_notice({"en": en, "terms": n["terms"], "tr": {"ko": ko, "ja": "あ", "es": "a"}, "prob": n.get("prob")}, g)
        iss = [x for x in iss if x["lang"] in ("en", "ko")]
        blank = [t for t in n["terms"] if not g[t].get("ko")]
        print(n["id"], "이슈", len(iss), iss if iss else "", "| ko 미기입 용어:", blank)


if __name__ == "__main__":
    main()
