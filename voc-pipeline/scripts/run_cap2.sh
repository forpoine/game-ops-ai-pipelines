#!/bin/bash
# cap2 재측정(02 4단계): 새 심각도 경계 규칙 프롬프트 + 정답 v3. Gemma 먼저, 그다음 gpt-oss(두 LLM 동시 로드 금지). 합성 데이터.
# 사용: nohup bash scripts/run_cap2.sh > data/cap2_run.log 2>&1 < /dev/null &   (끝나면 data/cap2_v3.done 생성)
cd "$(dirname "$0")/.." || exit 1
export PYTHONIOENCODING=utf-8 VOC_PROMPT=cap2
rm -f data/cap2_v3.done
run() { VOC_GOLD=$3 python scripts/classify.py "$1" "$2" > "data/classify_$2.log" 2>&1; }
lms unload --all
lms load google/gemma-4-12b-qat -y
run google/gemma-4-12b-qat gemma_cap2 syn_voc_gold_v3.csv
run google/gemma-4-12b-qat gemma_b_cap2 syn_voc_b_gold_v3.csv
lms unload --all
lms load openai/gpt-oss-20b -y
run openai/gpt-oss-20b gptoss_cap2 syn_voc_gold_v3.csv
run openai/gpt-oss-20b gptoss_b_cap2 syn_voc_b_gold_v3.csv
touch data/cap2_v3.done
echo done
