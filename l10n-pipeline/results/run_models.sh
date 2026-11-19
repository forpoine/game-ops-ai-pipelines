#!/bin/sh
# gpt-oss 20B -> Qwen3 14B 순서로 측정(n=40, baseline/protected) + 공지 5종 번역. 모델은 한 번에 하나만 로드.
export PYTHONIOENCODING=utf-8
LMS="${LMS:-lms}"  # LM Studio CLI (PATH에 없으면 LMS=경로 로 지정)
cd "$(dirname "$0")/.."
run() { # $1 모델 id, $2 파일 접두
  $LMS unload --all > /dev/null 2>&1
  $LMS load "$1" -y > results/load_$2.txt 2>&1
  python scripts/measure.py --model "$1" --mode baseline  --n 40 > results/log_$2_baseline.txt 2>&1
  python scripts/measure.py --model "$1" --mode protected --n 40 > results/log_$2_protected.txt 2>&1
  python scripts/translate_notices.py --model "$1" > results/log_$2_notices.txt 2>&1
}
run openai/gpt-oss-20b gptoss
NOTHINK=1 run qwen3-14b qwen
$LMS unload --all > /dev/null 2>&1
touch results/models.done
