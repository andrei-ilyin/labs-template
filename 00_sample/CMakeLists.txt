cmake_minimum_required(VERSION 3.5)

project(solution)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

if (MINGW)
    set(THREADS_OPTION "-mthreads")
else (MINGW)
    set(THREADS_OPTION "-pthread")
endif (MINGW)

if (MINGW)
    set(CODE_COVERAGE_OPTION "")
else (MINGW)
    set(CODE_COVERAGE_OPTION "-fprofile-instr-generate -fcoverage-mapping")
endif (MINGW)

if (MINGW)
    set(SANITIZER_OPTION "")
else (MINGW)
    set(SANITIZER_OPTION "-fsanitize=address,undefined")
endif (MINGW)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${CODE_COVERAGE_OPTION} ${SANITIZER_OPTION} -fPIC -Wall -Wextra -Wno-sign-compare -Wno-attributes -g")
set(CMAKE_EXE_LINKER_FLAGS ${CMAKE_EXE_LINKER_FLAGS} "${THREADS_OPTION}")

# Prevent unnecessary I/O operations during dev runs by disable success
# tracking mechanism (success token file creation).
add_definitions(-DDISABLE_SUCCESS_TRACKER)

# Ignore main() in student's solution
add_definitions(-DIGNORE_SOLUTION_MAIN)

# Common cross-lab files
include_directories(${CMAKE_SOURCE_DIR}/../common)

# Student's solution
include_directories(${CMAKE_SOURCE_DIR})
include_directories(${CMAKE_SOURCE_DIR}/solution_src)

FILE(GLOB SolutionSrcs solution_src/*.cpp)
list(FILTER SolutionSrcs EXCLUDE REGEX ".*_tests\\.cpp$")

# Teacher's tests and additional files
include_directories(${CMAKE_SOURCE_DIR}/tests_src)

FILE(GLOB TestSrcs tests_src/*.cc)
list(FILTER TestSrcs EXCLUDE REGEX ".*bench.*")

FILE(GLOB BenchSrcs tests_src/*.cc)
list(FILTER BenchSrcs EXCLUDE REGEX ".*tests.*")

# These tests will be ran on server.
add_executable(
        server_tests

        ${SolutionSrcs}
        ${TestSrcs}

        ../common/utils/utils.cc
        ../common/gtest/gtest-all.cc
        ../common/gmock/gmock-all.cc
        ../common/gmock/gmock_main.cc
)

# These benchmarks will be ran on server.
#    add_executable(
#            server_bench
#
#            ${SolutionSrcs}
#            ${BenchSrcs}
#
#            ../common/utils/utils.cc
#            ../common/benchmark/benchmark-all.cc
#            ../common/benchmark/benchmark_main.cc
#    )
