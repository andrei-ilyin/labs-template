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
    ./make_package.sh $LAB_NAME
else
    ./make_package.sh --no-precompile $LAB_NAME
fi;

unzip $LAB_NAME/package-yacontest.zip -d temp/
cp $LAB_NAME/build.sh temp/

if (( $USE_ZIP )); then
    echo "Solution compiler: ZIP"
    zip -j temp/solution.zip $LAB_NAME/solution_src/*
else
    echo "Solution compiler: CPP"
    cp $LAB_NAME/solution_src/solution.cpp temp/
fi

cd temp/
echo 'private' > INPUT_FILE_NAME
make
make run
