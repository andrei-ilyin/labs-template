cmake_minimum_required(VERSION 3.5)

enable_language(ASM_NASM)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

if (MINGW)
    set(THREADS_OPTION "-mthreads")
else (MINGW)
    set(THREADS_OPTION "-pthread")
endif (MINGW)

if (MINGW)
    set(PIE_OPTION "-no-pie")
else (MINGW)
    set(PIE_OPTION "")
endif (MINGW)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${PIE_OPTION} -Wall -Wextra -Wno-sign-compare -Wno-attributes -g")
set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} ${THREADS_OPTION} -fno-omit-frame-pointer")

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

# Additional helpers for assembly testing
add_library(asm_utils STATIC common/utils/asm_utils.asm)
