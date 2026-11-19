#!/bin/sh
# 공지체 틀(--tpl notice)로 몬헌 100문장 3모델 측정. run_mhw.sh가 끝난 뒤 실행.
export PYTHONIOENCODING=utf-8
LMS="${LMS:-lms}"  # LM Studio CLI (PATH에 없으면 LMS=경로 로 지정)
cd "$(dirname "$0")/.."
run() {
  $LMS unload --all > /dev/null 2>&1
  $LMS load "$1" -y > results/load_mhwn_$2.txt 2>&1
  for mode in baseline protected; do
    python scripts/measure.py --glossary mhw --tpl notice --model "$1" --mode $mode --n 100 > results/log_mhwn_$2_$mode.txt 2>&1
  done
}
$LMS server start > /dev/null 2>&1
run openai/gpt-oss-20b gptoss
NOTHINK=1 run qwen3-14b qwen
run google/gemma-4-12b-qat gemma
touch results/mhw_notice.done
