cmake_minimum_required(VERSION 3.5)

project(cpp-labs)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

if (MINGW)
    set(THREADS_OPTION "-mthreads")
else (MINGW)
    set(THREADS_OPTION "-pthread")
endif (MINGW)

if (CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    set(CODE_COVERAGE_OPTION "-fprofile-instr-generate -fcoverage-mapping")
else ()
    set(CODE_COVERAGE_OPTION "")
endif ()

if (CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    set(SANITIZER_OPTION "-fsanitize=address,leak,undefined -fno-sanitize-recover=all")
else ()
    set(SANITIZER_OPTION "")
endif ()

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${CODE_COVERAGE_OPTION} ${SANITIZER_OPTION} -fPIC -Wall -Wextra -Wno-sign-compare -Wno-attributes -g")
set(CMAKE_EXE_LINKER_FLAGS ${CMAKE_EXE_LINKER_FLAGS} "${THREADS_OPTION}")

# Prevent unnecessary I/O operations during dev runs by disable success
# tracking mechanism (success token file creation).
add_definitions(-DDISABLE_SUCCESS_TRACKER)

# Ignore main() in student's solution
add_definitions(-DIGNORE_SOLUTION_MAIN)

# Common cross-lab files
include_directories(${CMAKE_SOURCE_DIR}/common)

# These object files will be later linked with tests executables.
add_library(gtest_files OBJECT
        common/gtest/gtest-all.cc
        common/gmock/gmock-all.cc
        common/gmock/gmock_main.cc
        common/utils/utils.cc)

# Labs subprojects
add_subdirectory(00_sample)
