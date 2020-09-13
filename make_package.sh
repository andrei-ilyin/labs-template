#!/usr/bin/env bash

set -e

if [[ $1 == "--no-precompile" ]]; then
    PRECOMPILE=0
    LAB_NAME=$2
else
    PRECOMPILE=1
    LAB_NAME=$1
fi

rm $LAB_NAME/package.zip || true

zip -j $LAB_NAME/package.zip $LAB_NAME/tests_src/* $LAB_NAME/tester_config.py

cd common
zip -r ../$LAB_NAME/package.zip cpplint/ gtest/ gmock/ testerlib/ utils/
if (( $PRECOMPILE )); then
    ../$LAB_NAME/build.sh --precompile $PWD $PWD/obj $PWD/../$LAB_NAME/package.zip
fi

# You can comment the following lines if you don't need Yandex.Contest package
cd ../$LAB_NAME/
mv package.zip package_zip
zip -j package-yacontest.zip package_zip build.sh ../common/yacontest/Makefile ../common/yacontest/run_build.sh
mv package_zip package.zip
