cmake_minimum_required(VERSION 3.5)

project(labs-template)

# This config should be used for C++ labs
include(${CMAKE_CURRENT_SOURCE_DIR}/cpp.cmake)

# This config should be used for NASM labs
#include(${CMAKE_CURRENT_SOURCE_DIR}/nasm.cmake)

# Labs subprojects
add_subdirectory(00_sample)
