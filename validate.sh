#!/usr/bin/env bash

set -e
shopt -s nullglob

# Process command line args

RUNNER_ARGS=("${@}")

PRECOMPILE=1
if [[ "${RUNNER_ARGS[0]}" == "--no-precompile" ]]; then
    PRECOMPILE=0
    RUNNER_ARGS=("${RUNNER_ARGS[@]:1}")
fi

FORCE_ZIP=0
if [[ "${RUNNER_ARGS[0]}" == "--force-zip" ]]; then
    FORCE_ZIP=1
    RUNNER_ARGS=("${RUNNER_ARGS[@]:1}")
fi

LAB_NAME="${RUNNER_ARGS[0]}"
RUNNER_ARGS=("${RUNNER_ARGS[@]:1}")

if [[ -z $LAB_NAME ]]; then
  echo "Usage: validate.sh [--no-precompile] [--force-zip] LAB_NAME [ARGS_TO_RUNNER_PY...]"
  exit 1
fi

echo "Use ZIP for solution validation: $FORCE_ZIP"

# Detect solution source files and used language

solution_dir=$LAB_NAME
if [[ -d $LAB_NAME/solution_src ]]; then
  solution_dir=$LAB_NAME/solution_src
fi
echo "Solution dir: $solution_dir"

solution_files=""
solution_lang=""
if [[ -f $solution_dir/solution.cpp ]] && (( $FORCE_ZIP == 0 )); then
  solution_files=$solution_dir/solution.cpp
  solution_lang=CPP
elif [[ -f $solution_dir/solution.asm ]] && (( $FORCE_ZIP == 0 )); then
  solution_files=$solution_dir/solution.asm
  solution_lang=ASM
elif ls $solution_dir/*.{cpp,h,asm} 1>/dev/null 2>&1; then
  solution_files=$(echo $solution_dir/*.{cpp,h,asm})
  solution_lang=ZIP
else
  echo "No solution source files detected"
  exit 1
fi
echo "Solution files: $solution_files"
echo "Solution compiler: $solution_lang"

# Prepare TEMP directory

mkdir -p temp/
rm -rf temp/*

# Prepare package

if (( $PRECOMPILE )); then
    ./make_package.sh $LAB_NAME
else
    ./make_package.sh --no-precompile $LAB_NAME
fi;

cp $LAB_NAME/package.zip temp/
cp $LAB_NAME/build.sh temp/

# Prepare and build solution

case $solution_lang in
  "ZIP")
    zip -j temp/solution.zip $solution_files
    cd temp/
    ./build.sh solution.zip package.zip $PWD/tmp $PWD/exe ZIP
    ;;
  "CPP" | "ASM")
    cp $solution_files temp/
    cd temp/
    ./build.sh solution.* package.zip $PWD/tmp $PWD/exe $solution_lang
    ;;
  *)
    echo "ERROR: Undefined language $solution_lang"
    exit 1
    ;;
esac

# Run testing
# NOTE: to check tester config with your eyes, add  --print-test-config option
cd exe/
./runner.py --verbose-testing --mode=irunner --irunner-report-json=$PWD/../irunner_report.json --print-report-to-stderr --time-limit-debug "${RUNNER_ARGS[@]}"
