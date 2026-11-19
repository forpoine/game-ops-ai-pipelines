"""공지 번역 검수기 (LLM 없음, 규칙만).
입력: 영어 원문 + 언어별 번역(ko/ja/es) + 용어 ID 목록 + 글자 수 한도.
검사 6종:
  term      용어집 공식명이 번역에 그대로 들어 있는가
  number    원문 숫자(날짜·시간 포함)가 번역에 같은 개수로 있는가
  missing   번역이 비었거나 해당 언어 문자가 아닌가
  overflow  글자 수가 한도를 넘는가(Photoshop 글자 영역 수치에서 환산한 값)
  prob      확률 표의 합이 100%인가(원문과 번역 모두)
  leftover  치환되지 않은 자리표시자([[T1]], {T:id})가 남았는가
사용: from checker import check_notice
"""
import csv, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ["ko", "ja", "es"]

HANGUL = re.compile(r"[가-힣]")
KANA = re.compile(r"[぀-ヿ]")
NUM = re.compile(r"\d+(?:[.,]\d+)?")
ALLOWED_LATIN = {"KST", "UTC", "HP", "ID", "SERVICE"}  # ko/ja 본문에 영어로 남아도 되는 약어
PROB = re.compile(r"(\d+(?:\.\d+)?)\s*%")


def load_glossary(path=None):
    """포켓몬(PokéAPI) + 몬헌(사용자 기입, ko 칸 비면 검사 제외) 합본. api_id가 키."""
    paths = [Path(path)] if path else [ROOT / "glossary" / "pokeapi_terms.csv",
                                       ROOT / "glossary" / "몬헌_기입용.csv",
                                       ROOT / "glossary" / "가상_서비스용어.csv"]
    out = {}
    for p in paths:
        if p.exists():
            with p.open(encoding="utf-8-sig") as f:
                out.update({r["api_id"]: r for r in csv.DictReader(f)})
    return out


def nums(text):
    # 천 단위 쉼표 제거(1,000 -> 1000), 소수점은 유지
    return sorted(re.sub(r",(?=\d{3}\b)", "", n) for n in NUM.findall(text))


MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
WORD_NUM = {"doubled": "2", "double": "2", "twice": "2", "tripled": "3", "triple": "3"}


def words_to_digits(en):
    """영어 원문의 월 이름(November -> 11)과 배수 단어(doubled -> 2)를 숫자로 바꿔 번역의 '11월', '2배'와 맞춘다."""
    for i, m in enumerate(MONTHS, 1):
        en = re.sub(rf"\b{m}\b", str(i), en)
    return re.sub(r"\b(" + "|".join(WORD_NUM) + r")\b", lambda m: WORD_NUM[m.group(1).lower()], en, flags=re.I)


ES_MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
             "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def es_words_to_digits(es):
    """스페인어 번역의 월 이름(noviembre -> 11)과 배수 단어(duplicará -> 2)를 숫자로 바꿔 원문 숫자와 맞춘다."""
    for i, m in enumerate(ES_MONTHS, 1):
        es = re.sub(rf"\b{m}\b", str(i), es, flags=re.I)
    es = re.sub(r"\b(primer[oa]?|primero)\b", "1", es, flags=re.I)  # 서수 단어(1st -> primer lugar)
    for w, d in (("segund[oa]", 2), ("tercer[oa]?", 3), ("cuart[oa]", 4), ("quint[oa]", 5), ("d[eé]cim[oa]", 10)):
        es = re.sub(rf"\b{w}\b", str(d), es, flags=re.I)
    es = re.sub(r"\b(duplic\w*|doble|dos veces)\b", "2", es, flags=re.I)
    return re.sub(r"\b(triplic\w*|triple)\b", "3", es, flags=re.I)


def ja_dates_times(ja):
    """일본어의 현지화된 날짜·시각을 원문 형식으로 되돌려 비교한다: 2026年12月3日 -> 2026-12-03, 午前2時 -> 02:00, 午後8時 -> 20:00."""
    ja = re.sub(r"(\d{4})年(\d{1,2})月(\d{1,2})日", lambda m: f"{m[1]}-{int(m[2]):02d}-{int(m[3]):02d} ", ja)
    def t(m):
        h, mi = int(m[2]), int(m[3] or 0)
        if m[1] == "午後" and h < 12:
            h += 12
        return f"{h:02d}:{mi:02d}"
    ja = ja.replace("倍増", "2倍")  # doubled -> 倍増(숫자 없이 '두 배')
    return re.sub(r"(午前|午後)?(\d{1,2})時(?!間)(?:(\d{1,2})分)?", t, ja)


def lang_ok(lang, text):
    if not text.strip():
        return False
    if lang == "ko":
        return bool(HANGUL.search(text))
    if lang == "ja":
        return bool(KANA.search(text)) and not HANGUL.search(text)
    if lang == "es":
        return not (HANGUL.search(text) or KANA.search(text))
    return True


def prob_sum(text):
    vals = [float(x) for x in PROB.findall(text)]
    return round(sum(vals), 4) if vals else None


def check_notice(notice, glossary, limits=None):
    """notice: {"en": str, "terms": [api_id...], "tr": {"ko": str, ...}, "prob": bool}
    limits: {"ko": 글자수, ...}. 반환: [{"lang","kind","detail"}...]"""
    issues = []
    en = notice["en"]
    src_nums = nums(words_to_digits(en))
    if notice.get("prob"):
        s = prob_sum(en)
        if s is not None and abs(s - 100) > 1e-6:
            issues.append({"lang": "en", "kind": "prob", "detail": f"원문 확률 합 {s}%"})
    for lg in LANGS:
        text = notice["tr"].get(lg, "")
        if not lang_ok(lg, text):
            issues.append({"lang": lg, "kind": "missing", "detail": "비었거나 해당 언어 문자가 없음"})
            continue
        for tid in notice.get("terms", []):
            official = glossary[tid].get(lg, "")
            if not official:  # 사용자가 아직 기입하지 않은 칸은 검사하지 않음
                continue
            if official.replace(" ", "") not in text.replace(" ", ""):
                issues.append({"lang": lg, "kind": "term", "detail": f"{tid}: 공식명 '{official}' 없음"})
        if re.search(r"\[\[T\d+\]\]|\{T:[^}]+\}", text):
            issues.append({"lang": lg, "kind": "leftover", "detail": "자리표시자가 남음"})
        # 일본어는 원문에 없는 "1人/1日/1回/1つ"를 관용적으로 붙인다(Each trainer -> 1人につき). 오탐이라 제외.
        if lg in ("ko", "ja"):  # 번역 안 된 영어 단어(Evening Lake, Hunter Box, 3rd 등). 공식명·허용어는 제외한 뒤 남은 것을 경고
            rest = text
            for tid in notice.get("terms", []):
                official = glossary[tid].get(lg, "")
                if official:
                    rest = rest.replace(official, " ")
            rest = re.sub(r"\{SERVICE\}|\[\[T\d+\]\]|\{T:[^}]+\}", " ", rest)
            words = [w for w in re.findall(r"[A-Za-z]{2,}", rest) if w not in ALLOWED_LATIN]
            if words:
                issues.append({"lang": lg, "kind": "english", "detail": "번역 안 된 영어: " + ", ".join(words)})
        tn = nums(re.sub(r"(?<![\d.,:-])1(?=[人日回つ個名])", "", ja_dates_times(text))) if lg == "ja" else \
            nums(es_words_to_digits(text)) if lg == "es" else nums(text)
        if lg == "ja" and "1" in src_nums:
            tn = nums(ja_dates_times(text))  # 원문에 1이 있으면 그대로 비교
        if tn != src_nums:
            only_src = [n for n in src_nums if n not in tn]
            only_tr = [n for n in tn if n not in src_nums]
            issues.append({"lang": lg, "kind": "number",
                           "detail": f"원문에만 {only_src}, 번역에만 {only_tr}"})
        if notice.get("prob"):
            s = prob_sum(text)
            if s is None or abs(s - 100) > 1e-6:
                issues.append({"lang": lg, "kind": "prob", "detail": f"번역 확률 합 {s}%"})
        if limits and lg in limits and len(text) > limits[lg]:
            issues.append({"lang": lg, "kind": "overflow",
                           "detail": f"{len(text)}자 > 한도 {limits[lg]}자"})
    return issues
