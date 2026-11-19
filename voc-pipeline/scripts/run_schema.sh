#!/bin/bash
# 2026-11-19 JSON 스키마 강제 실험: Gemma Set A cap2, 재시도 없음(이전 gemma_cap2와 같은 조건 + response_format만 추가). 합성 데이터.
# 사용: nohup bash scripts/run_schema.sh > data/schema_run.log 2>&1 < /dev/null &   (끝나면 data/schema.done)
cd "$(dirname "$0")/.." || exit 1
export PYTHONIOENCODING=utf-8 VOC_PROMPT=cap2 VOC_GOLD=syn_voc_gold_v3.csv VOC_SCHEMA=1 VOC_RETRY=0
rm -f data/schema.done
python scripts/classify.py google/gemma-4-12b-qat gemma_cap2_schema > data/classify_gemma_cap2_schema.log 2>&1
touch data/schema.done
