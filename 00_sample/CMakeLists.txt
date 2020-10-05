project(00_sample)

# Student's solution
include_directories(${CMAKE_CURRENT_SOURCE_DIR})
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/solution_src)

FILE(GLOB SolutionSrcs solution_src/*.cpp)
list(FILTER SolutionSrcs EXCLUDE REGEX ".*_tests\\.cpp$")

# Teacher's tests and additional files
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/tests_src)

FILE(GLOB TestSrcs tests_src/*.cc)
list(FILTER TestSrcs EXCLUDE REGEX ".*bench.*")

FILE(GLOB BenchSrcs tests_src/*.cc)
list(FILTER BenchSrcs EXCLUDE REGEX ".*tests.*")

# These tests will be ran on server.
add_executable(${PROJECT_NAME} ${SolutionSrcs} ${TestSrcs})
add_dependencies(${PROJECT_NAME} gtest_files)
target_link_libraries(${PROJECT_NAME} gtest_files)
