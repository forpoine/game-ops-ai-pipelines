#!/bin/sh
# 몬헌 용어(검수된 288개 중 100문장) 3모델 측정. 모델은 한 번에 하나만 로드.
export PYTHONIOENCODING=utf-8
LMS="${LMS:-lms}"  # LM Studio CLI (PATH에 없으면 LMS=경로 로 지정)
cd "$(dirname "$0")/.."
run() { # $1 모델 id, $2 파일 접두
  $LMS unload --all > /dev/null 2>&1
  $LMS load "$1" -y > results/load_mhw_$2.txt 2>&1
  python scripts/measure.py --glossary mhw --model "$1" --mode baseline  --n 100 > results/log_mhw_$2_baseline.txt 2>&1
  python scripts/measure.py --glossary mhw --model "$1" --mode protected --n 100 > results/log_mhw_$2_protected.txt 2>&1
}
$LMS server start > /dev/null 2>&1
run openai/gpt-oss-20b gptoss
NOTHINK=1 run qwen3-14b qwen
run google/gemma-4-12b-qat gemma
touch results/mhw.done
