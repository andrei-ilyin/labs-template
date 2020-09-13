#!/usr/bin/env bash

# set -x
set -e
set -o pipefail

mkdir ./src ./temp
mv package_zip ./src/package.zip

count=`ls -1 *.zip 2>/dev/null | wc -l`
if [ $count != 0 ]; then
  mv *.zip ./src/solution.zip || true;
  ./build.sh $PWD/src/solution.zip $PWD/src/package.zip $PWD/temp/ $PWD ZIP;
else
   mv *.cpp ./src/solution.cpp || true;
  ./build.sh $PWD/src/solution.cpp $PWD/src/package.zip $PWD/temp/ $PWD CPP;
fi;

rm -rf ./src ./temp
