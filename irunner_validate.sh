#!/usr/bin/env bash

set -e

mkdir -p temp/
rm -rf temp/*

RUNNER_ARGS=("${@}")

PRECOMPILE=1
if [[ $1 == "--no-precompile" ]]; then
    PRECOMPILE=0
    RUNNER_ARGS=("${RUNNER_ARGS[@]:1}")
fi

USE_ZIP=1
if [[ "$1" == "--no-zip" ]]; then
    USE_ZIP=0
    RUNNER_ARGS=("${RUNNER_ARGS[@]:1}")
fi

LAB_NAME=$RUNNER_ARGS
RUNNER_ARGS=("${RUNNER_ARGS[@]:1}")

if (( $PRECOMPILE )); then
    ./irunner_make_package.sh $LAB_NAME
else
    ./irunner_make_package.sh --no-precompile $LAB_NAME
fi;

cp $LAB_NAME/package.zip temp/
cp $LAB_NAME/build.sh temp/

if (( $USE_ZIP )); then
    echo "Solution compiler: ZIP"
    zip -j temp/solution.zip $LAB_NAME/solution_src/*
    cd temp/
    ./build.sh solution.zip package.zip $PWD/tmp $PWD/exe ZIP
else
    echo "Solution compiler: CPP"
    cp $LAB_NAME/solution_src/solution.cpp temp/
    cd temp/
    ./build.sh solution.cpp package.zip $PWD/tmp $PWD/exe CPP
fi

cd exe/
./runner.py --verbose --mode=irunner --irunner-report-json=$PWD/../irunner_report.json --print-report-to-stderr "${RUNNER_ARGS[@]}"
