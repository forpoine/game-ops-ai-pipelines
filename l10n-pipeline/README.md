# l10n-pipeline

용어 보호 방식의 다국어(한·영·일·스페인어) 공지 파이프라인 + 규칙 기반 자동 검수. 서비스는 가상(`{SERVICE}`), 용어는 몬스터헌터·포켓몬의 텍스트 데이터만 사용한다(이미지·로고 없음). 일본어는 사람이 검증하지 않았다.

## 흐름
원문에 용어 ID 표시(`{T:potion}`) → LLM에는 `[[T1]]` 자리표시자만 보내 주변 문장만 번역 → 언어별 공식명을 코드로 삽입 → 검수기(용어, 숫자·날짜, 언어 누락, 글자 수, 확률 합 100%, 자리표시자 잔존) → 사람 승인 리포트.

## 폴더
- `glossary/pokeapi_terms.csv` 포켓몬·아이템 552개(영·한·일·스페인어, PokéAPI). `glossary/몬헌_기입용.csv` 몬헌 6개(ko 사용자 확정, ja/es는 팬 사이트 게임 데이터 표). `glossary/용어집_초안.csv` 몬헌 전체 후보(ko 미기입).
- `notices/notices_src.json` 공지 5종 원문(영·한). `notices/translated_<모델>.json` 모델별 번역과 검수 결과.
- `results/` 측정 결과(`<모델>_baseline|protected.json`), 로그, `baseline_분석.md`. `results/prev_run1/`은 이전 실행 백업.
- `out/` 생성 HTML(`summary.html` 모델 비교, `report_<모델>.html` 승인용 리포트, `manual_test.html` 수작업 시험지).
- `case/CASE_초안.md` 케이스 초안(KR+EN). `HANDOFF.md` 진행 기록.

## 실행 (LM Studio 서버 `http://localhost:1234/v1`, 모델은 한 번에 하나만 로드)
```bash
export PYTHONIOENCODING=utf-8
python scripts/fetch_pokeapi.py                                   # 용어집(이미 있음, 캐시 사용)
python scripts/measure.py --model google/gemma-4-12b-qat --mode baseline --n 40   # 또는 protected
python scripts/translate_notices.py --model google/gemma-4-12b-qat                # 공지 5종 번역+검수
# Qwen3는 NOTHINK=1 을 앞에 붙임(프롬프트 끝 /no_think)
```
LLM 없이 되는 것:
```bash
python scripts/compare.py            # 모델 비교표(콘솔)
python scripts/analyze_baseline.py   # 오답 유형
python scripts/plant_errors.py       # 심은 오류 10개 검출률
python scripts/test_checker.py       # 검수기 단위 테스트
python scripts/build_outputs.py      # out/ HTML 생성
python scripts/make_manual_test.py   # 수작업 시험지(정답은 out/manual_answer_key.json)
python scripts/score_manual.py "<시험지 결과 글>"   # 시험지 채점
```
reasoning 모델이라 `max_tokens`가 모자라면 빈 출력이 나온다(실측: 4000에서 일부 빈 출력). 번역은 7000으로 돌린다.
