#!/bin/bash
# Gemma 형식 실패 대응(2026-11-18 사용자 결정 "설정 늘려 재측정"): 컨텍스트 16384, max_tokens 12000으로 cap2를 정답 v3에 다시 잰다.
# 앞선 max_tokens 4000·컨텍스트 8192 결과(gemma_cap2, gemma_b_cap2)는 그대로 두고 따로 보고한다. 합성 데이터.
# 사용: nohup bash scripts/run_gemma_long.sh > data/gemma_long_run.log 2>&1 < /dev/null &   (끝나면 data/gemma_long.done)
cd "$(dirname "$0")/.." || exit 1
export PYTHONIOENCODING=utf-8
rm -f data/gemma_long.done
lms unload --all
lms load google/gemma-4-12b-qat -c 16384 -y
lms ps
VOC_PROMPT=cap2 VOC_MAX_TOKENS=12000 VOC_GOLD=syn_voc_gold_v3.csv python scripts/classify.py google/gemma-4-12b-qat gemma_cap2_long > data/classify_gemma_cap2_long.log 2>&1
VOC_PROMPT=cap2 VOC_MAX_TOKENS=12000 VOC_GOLD=syn_voc_b_gold_v3.csv python scripts/classify.py google/gemma-4-12b-qat gemma_b_cap2_long > data/classify_gemma_b_cap2_long.log 2>&1
touch data/gemma_long.done
echo done
