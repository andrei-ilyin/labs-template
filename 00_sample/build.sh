#!/usr/bin/env bash

# set -x
set -e
set -o pipefail

CXX="clang++-10"
CXX_FLAGS="-std=c++17 -pthread -fPIC -Wall -Wextra -Wno-sign-compare -Wno-attributes -DIGNORE_SOLUTION_MAIN"
CXX_FLAGS_DBG="$CXX_FLAGS -O0"
CXX_FLAGS_OPT="$CXX_FLAGS -O2"
CXX_FLAGS_ASAN="$CXX_FLAGS -O2 -g -fno-omit-frame-pointer -fsanitize=address,leak,undefined -fno-sanitize-recover=all"
CXX_FLAGS_MSAN="$CXX_FLAGS -O2 -g -fno-omit-frame-pointer -fsanitize=memory"

LINK_FLAGS="-Wl,-z,stack-size=268435456"

function build_solution {
    SOLUTION_FILE=${1:-SOLUTION_FILE}
    TEST_ZIP=${2:-TEST_ZIP}
    TEMP_DIR=${3:-TEMP_DIR}
    OUTPUT_DIR=${4:-OUTPUT_DIR}
    COMPILER=${5:-COMPILER}

    mkdir -p $TEMP_DIR
    mkdir -p $OUTPUT_DIR

    # Zip archives extraction

    SOLUTION_SRC_DIR=$TEMP_DIR/solution_src
    SOLUTION_SRCS="$SOLUTION_SRC_DIR/file.cpp $SOLUTION_SRC_DIR/other_file.cpp"
    SOLUTION_HDRS="$SOLUTION_SRC_DIR/file.h"
    if [[ "$COMPILER" == "ZIP" ]]; then
        unzip -qq -DD -o -d $SOLUTION_SRC_DIR $SOLUTION_FILE &>/dev/null
    else
        echo This lab supports only ZIP compiler!
        exit 1
        # mkdir -p $SOLUTION_SRC_DIR
        # cp $SOLUTION_FILE $SOLUTION_SRC_DIR/
    fi

    TEST_SRC_DIR=$TEMP_DIR/tests_src
    TEST_SRCS="$TEST_SRC_DIR/*.cc $TEST_SRC_DIR/utils/utils.cc"
    unzip -qq -DD -o -d $TEST_SRC_DIR $TEST_ZIP &>/dev/null

    # Source code pre-compile check

    python3 \
      $TEST_SRC_DIR/cpplint/cpplint.py \
      --filter='-build/include,-runtime/int,-build/include_subdir,-legal/copyright,-build/c++11,-runtime/references' \
      --repository=$SOLUTION_SRC_DIR \
      $SOLUTION_SRCS $SOLUTION_HDRS 2>&1 \
    | sed "s|$SOLUTION_SRC_DIR/||g" \
    | perl -ne 'print if not /Done processing/'

    # Compilation

    function remove_paths_from_log {
        sed -i "s|$SOLUTION_SRC_DIR/||g" $1
        sed -i "s|$TEST_SRC_DIR/||g" $1
        perl -i -ne 'print if not (/gtest/ or /gmock/)' $1
    }

    function compile_tests {
        local CXX_CMD="$CXX -I$TEST_SRC_DIR -I$SOLUTION_SRC_DIR -I$TEMP_DIR $1"
        local COMPILE_DIR=$TEMP_DIR/$2
        local PRECOMPILED_OBJ_DIR=$TEST_SRC_DIR/$2
        local OUT_EXE=$3

        mkdir -p $COMPILE_DIR
        cd $COMPILE_DIR

        touch solution_compiler_output.log
        if [[ -n `$CXX_CMD -c $SOLUTION_SRCS &> solution_compiler_output.log || echo $?` ]]; then
            remove_paths_from_log solution_compiler_output.log
            grep -e note -e warning -e error solution_compiler_output.log && false;
        fi;

        touch tests_compiler_output.log
        if [[ -n `$CXX_CMD -c $TEST_SRCS &> tests_compiler_output.log || echo $?` ]]; then
            remove_paths_from_log tests_compiler_output.log
            grep -e note -e warning -e error tests_compiler_output.log && false;
        fi;

        if [[ -d $PRECOMPILED_OBJ_DIR ]]; then
            cp $PRECOMPILED_OBJ_DIR/* ./
        fi
        function compile_if_missing {
            if [[ ! -f $2 ]]; then
                $CXX_CMD -c $TEST_SRC_DIR/$1 -o $2 &> tests_compiler_output.log
            fi
        }

        compile_if_missing gtest/gtest-all.cc gtest.o
        compile_if_missing gmock/gmock-all.cc gmock.o
        compile_if_missing gmock/gmock_main.cc gmock_main.o

        touch linker_output.log
        if [[ -n `( \
                    $CXX_CMD $LINK_FLAGS *.o -o $OUT_EXE 2>&1 \
                    | perl -ne 'print if not (/gtest/ or /[a-zA-Z0-9_]+[.]o[:]/)' \
                  ) &>linker_output.log || echo $?` ]]; then
            remove_paths_from_log linker_output.log;
            cat linker_output.log && false;
        fi;

        cd - &>/dev/null
    }

    compile_tests "$CXX_FLAGS_DBG" obj_dbg $OUTPUT_DIR/tests_dbg
    compile_tests "$CXX_FLAGS_OPT" obj_opt $OUTPUT_DIR/tests_opt
    compile_tests "$CXX_FLAGS_ASAN" obj_asan $OUTPUT_DIR/tests_asan
    # compile_tests "$CXX_FLAGS_MSAN" obj_msan $OUTPUT_DIR/tests_msan

    # Copy helper scripts

    cp $TEST_SRC_DIR/tester_config.py $OUTPUT_DIR/
    cp $TEST_SRC_DIR/testerlib/*.py $OUTPUT_DIR/
}

function precompile_libs {
    LIBS_DIR=${2:-LIBS_DIR}
    TEMP_DIR=${3:-TEMP_DIR}
    PACKAGE_ZIP=${4:-PACKAGE_ZIP}

    mkdir -p $TEMP_DIR
    cd $TEMP_DIR

    function precompile {
        local CXX_CMD="$CXX -I$LIBS_DIR $1"
        local COMPILE_DIR=$TEMP_DIR/$2

        mkdir -p $COMPILE_DIR
        cd $COMPILE_DIR

        $CXX_CMD -c $LIBS_DIR/gtest/gtest-all.cc -o gtest.o
        $CXX_CMD -c $LIBS_DIR/gmock/gmock-all.cc -o gmock.o
        $CXX_CMD -c $LIBS_DIR/gmock/gmock_main.cc -o gmock_main.o

        cd - &>/dev/null

        zip -r $PACKAGE_ZIP $2/
        rm -rf $2/
    }

    precompile "$CXX_FLAGS_DBG" obj_dbg
    precompile "$CXX_FLAGS_OPT" obj_opt
    precompile "$CXX_FLAGS_ASAN" obj_asan
    # precompile "$CXX_FLAGS_MSAN" obj_msan
}

if [[ $1 == "--precompile" ]]; then
    precompile_libs "$@"
else
    build_solution "$@"
fi
