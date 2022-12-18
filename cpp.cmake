cmake_minimum_required(VERSION 3.5)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 20)

if (MINGW)
    set(THREADS_OPTION "-mthreads")
else (MINGW)
    set(THREADS_OPTION "-pthread")
endif (MINGW)

if (CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    set(LIBCXX_OPTION "-stdlib=libc++")
else ()
    set(LIBCXX_OPTION "")
endif ()

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

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${LIBCXX_OPTION} ${CODE_COVERAGE_OPTION} ${SANITIZER_OPTION} ${SANITIZER_OPTION} -fPIC -Wall -Wextra -Wno-sign-compare -Wno-attributes -g")
set(CMAKE_EXE_LINKER_FLAGS ${CMAKE_EXE_LINKER_FLAGS} "${THREADS_OPTION}")

# Prevent unnecessary I/O operations during dev runs by disable success
# tracking mechanism (success token file creation).
add_definitions(-DDISABLE_SUCCESS_TRACKER)

# Ignore main() in student's solution
add_definitions(-DIGNORE_SOLUTION_MAIN)

# Disable time measurement macro and speed tests in debug mode
set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -DDISABLE_TIME_MEASUREMENT -DSKIP_SPEED_TESTS")

# Common cross-lab files
include_directories(${CMAKE_SOURCE_DIR}/common)

# These object files will be later linked with tests executables.
add_library(gtest_files STATIC
        common/gtest/gtest-all.cc
        common/gmock/gmock-all.cc
        common/gmock/gmock_main.cc
        common/utils/utils.cc)

