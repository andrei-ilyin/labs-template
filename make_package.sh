#!/usr/bin/env bash

set -eu
shopt -s nullglob

# Process command line args

if [[ $1 == "--no-precompile" ]]; then
  PRECOMPILE=0
  LAB_NAME=$2
else
  PRECOMPILE=1
  LAB_NAME=$1
fi

echo "Precompilation enabled: $PRECOMPILE"
echo "Lab assignment name: $LAB_NAME"

# Prepare the package with lab-specific files

# Uncomment the following line if you are using "full" files structure with
# "tests_src" subdir present in the lab directory:
#tests_files=$(echo $LAB_NAME/tests_src/*)

# Uncomment the following line if you are using "simplified" files structure
# with fixed set of files:
#tests_files="$LAB_NAME/tests.cpp $LAB_NAME/solution.h"

if [[ -z "$tests_files" ]]; then
  echo 'You should uncomment proper $tests_files specification before use'
  exit 1
fi

echo "Tests files: $tests_files"

rm $LAB_NAME/package.zip || true

zip -j $LAB_NAME/package.zip $tests_files $LAB_NAME/tester_config.py
if [[ -d "$LAB_NAME/tests_src/data" ]]; then
  cd $LAB_NAME/tests_src
  zip ../package.zip ./data/*
  cd - &>/dev/null
fi

# Add common files to the package

cd common
zip -r ../$LAB_NAME/package.zip --exclude='*.idea*' cpplint/ gtest/ gmock/ testerlib/ utils/
if (( $PRECOMPILE )); then
  ../$LAB_NAME/build.sh --precompile $PWD $PWD/obj $PWD/../$LAB_NAME/package.zip
fi

# You can comment the following lines if you don't need Yandex.Contest package
cd ../$LAB_NAME/
mv package.zip package_zip
zip -j package-yacontest.zip package_zip build.sh ../common/yacontest/Makefile ../common/yacontest/run_build.sh
mv package_zip package.zip
