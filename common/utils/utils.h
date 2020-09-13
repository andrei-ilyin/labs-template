// Copyright (c) 2019-2020 Andrei Ilyin, Andrei Nevero. All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are
// met:
//
//    * Redistributions of source code must retain the above copyright
// notice, this list of conditions and the following disclaimer.
//    * Redistributions in binary form must reproduce the above
// copyright notice, this list of conditions and the following disclaimer
// in the documentation and/or other materials provided with the
// distribution.
//    * Changes made to the source code must be documented if this code is
// published in a repository/storage with a public access.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
// "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
// LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
// A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
// OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
// SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
// LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
// DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
// THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
// (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
// OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

#ifndef UTILS_H_
#define UTILS_H_

#include <algorithm>
#include <cassert>
#include <chrono>
#include <cstdlib>
#include <cmath>
#include <future>
#include <random>
#include <string>

#ifdef __linux__
#include <sys/mman.h>
#include <unistd.h>
#elif _WIN32
#include <windows.h>
#include <memoryapi.h>
#endif

#include "gtest/gtest.h"

// ---------------------------------------------------------------------------
// Integration helpers

class TestSuccessTracker {
 public:
  TestSuccessTracker();
  ~TestSuccessTracker();
};

// ---------------------------------------------------------------------------
// Random

void SetRand64Seed(uint64_t new_seed);
uint64_t Rand64();

uint64_t URandom64(uint64_t min, uint64_t max);
int64_t SRandom64(int64_t min, int64_t max);

uint32_t URandom32(uint32_t min, uint32_t max);
int32_t SRandom32(int32_t min, int32_t max);

std::vector<int32_t> RandomInt32Array(
    size_t n, int32_t min = INT32_MIN, int32_t max = INT32_MAX);
std::vector<uint32_t> RandomUInt32Array(
    size_t n, uint32_t min = 0, uint32_t max = UINT32_MAX);
std::vector<int64_t> RandomInt64Array(
    size_t n, int64_t min = INT32_MIN, int64_t max = INT32_MAX);
std::vector<uint64_t> RandomUInt64Array(
    size_t n, uint64_t min = 0, uint64_t max = UINT64_MAX);

std::string RandomString(size_t n, int64_t min = 1, int64_t max = 127);

// ---------------------------------------------------------------------------
// Time

#define ASSERT_NOT_INFINITE_LOOP(timout_millis, stmt) {                        \
  std::promise<bool> completed;                                                \
  auto stmt_future = completed.get_future();                                   \
  std::thread([&](std::promise<bool>& completed) {                             \
    stmt;                                                                      \
    completed.set_value(true);                                                 \
  }, std::ref(completed)).detach();                                            \
  if (stmt_future.wait_for(std::chrono::milliseconds(timout_millis)) ==        \
      std::future_status::timeout) {                                           \
    std::string s = "\ttimed out (> " + std::to_string(timout_millis) +        \
        " milliseconds).";                                                     \
    FAIL() << s;                                                               \
  }                                                                            \
}

// Checks if user function execution time is no more than correct function
// execution time, multiplied by the constant.

#define ASSERT_DURATION_GE(correct_function, user_function)                    \
  ASSERT_DURATION_GE_A(correct_function, user_function, 2)

#define ASSERT_DURATION_GE_A(correct_function, user_function, time_constant) { \
  auto _correct_start_time = std::chrono::high_resolution_clock::now();        \
  correct_function;                                                            \
  auto _correct_end_time = std::chrono::high_resolution_clock::now();          \
                                                                               \
  auto _user_start_time = std::chrono::high_resolution_clock::now();           \
  user_function;                                                               \
  auto _user_end_time = std::chrono::high_resolution_clock::now();             \
                                                                               \
  auto _correct_exec_time =                                                    \
      1 + std::chrono::duration_cast<std::chrono::microseconds>(               \
          _correct_end_time - _correct_start_time).count();                    \
  auto _user_exec_time =                                                       \
      std::chrono::duration_cast<std::chrono::microseconds>(                   \
          _user_end_time - _user_start_time).count();                          \
                                                                               \
  if (time_constant * _correct_exec_time <= _user_exec_time) {                 \
    FAIL() << "\tTime limit exceeded.\n\tUser time: "                          \
           << std::to_string(_user_exec_time) << "\n\tAuthor time: "           \
           << std::to_string(_correct_exec_time);                              \
  }                                                                            \
}

// ---------------------------------------------------------------------------
// Exceptions

#define CATCH_EXCEPTION(function, expected_exc_type, expected_exc_what) {      \
  bool _thrown = false;                                                        \
  try {                                                                        \
    function;                                                                  \
  } catch (expected_exc_type& exc) {                                           \
    _thrown = true;                                                            \
    ASSERT_EQ(exc.what(), std::string(expected_exc_what));                     \
  } catch (...) {                                                              \
    _thrown = true;                                                            \
    FAIL() << "Expected: " #function " throws an exception of type "           \
          #expected_exc_type ".\n  Actual: it throws a different type.";       \
  }                                                                            \
  if (!_thrown) {                                                              \
    FAIL() << "Expected: " #function " throws an exception of type "           \
          #expected_exc_type ".\n  Actual: it throws nothing.";                \
  }                                                                            \
}

// ---------------------------------------------------------------------------
// Protected memory: General

template<typename T>
size_t AllocationSize(size_t n) {
  size_t bytes_allocated = n * sizeof(T);
  size_t page_size;

#ifdef __linux__
  page_size = getpagesize();
#elif _WIN32
  SYSTEM_INFO system_info;
  GetSystemInfo(&system_info);
  page_size = system_info.dwAllocationGranularity;
#endif

  while (bytes_allocated % page_size != 0) {
    ++bytes_allocated;
  }

  return bytes_allocated;
}

// ---------------------------------------------------------------------------
// Protected memory: 1D Arrays

template<typename T>
const T* AllocateROArray(const std::vector<T>& data) {
  T* result = nullptr;
  size_t bytes_allocated = AllocationSize<T>(data.size());
  size_t bytes_to_copy = sizeof(T) * data.size();

#ifdef __linux__
  result = (T*) mmap(nullptr, bytes_allocated, PROT_READ | PROT_WRITE,
                     MAP_PRIVATE | MAP_ANONYMOUS, 0, 0);

#elif _WIN32
  result = static_cast<T*>(VirtualAlloc(
      nullptr, bytes_allocated, MEM_COMMIT, PAGE_READWRITE));
#endif

  memcpy(result, data.data(), bytes_to_copy);
  for (size_t i = bytes_to_copy; i < bytes_allocated; ++i) {
    reinterpret_cast<char*>(result)[i] = (char) Rand64();
  }

#ifdef __linux__
  int mprotect_result = mprotect(result, bytes_allocated, PROT_READ);
  (void) mprotect_result;
  assert(mprotect_result == 0);
#elif _WIN32
  DWORD old_protect;
  DWORD mprotect_result = ::VirtualProtect(
      result, bytes_allocated, PAGE_READONLY, &old_protect);
  assert(mprotect_result);
#endif

  return result;
}

template<typename T>
void FreeROArray(const T* ptr, size_t n) {
#ifdef __linux__
  munmap((void*) ptr, AllocationSize<T>(n));
#elif _WIN32
  VirtualFree((void*) ptr, AllocationSize<T>(n), MEM_DECOMMIT);
#endif
}

template<typename T>
void RunTestOnROArray(const std::vector<T>& data,
                      const std::function<void(const T* ptr, size_t n)>& fn) {
  const T* ptr = AllocateROArray(data);
  fn(ptr, data.size());
  FreeROArray(ptr, data.size());
}

#define RUN_ON_RO_ARRAY(ElementType, data, fn)                                 \
  ASSERT_NO_FATAL_FAILURE(RunTestOnROArray<ElementType>(data, fn));

// ---------------------------------------------------------------------------
// Protected memory: 2D Arrays

template<typename T>
const T** AllocateROArray2D(const std::vector<std::vector<T>>& data) {
  std::vector<const T*> data_1d;
  for (const auto& data_row : data) {
    data_1d.push_back(AllocateROArray(data_row));
  }
  return const_cast<const T**>(AllocateROArray<const T*>(data_1d));
}

template<typename T>
void FreeROArray2D(const T** ptr, size_t n, size_t m) {
  for (size_t i = 0; i < n; ++i) {
    FreeROArray(ptr[i], m);
  }
  FreeROArray(ptr, n);
}

template<typename T>
void RunTestOnROArray2D(
    const std::vector<std::vector<T>>& data,
    const std::function<void(const T** ptr, size_t n, size_t m)>& fn) {
  assert(!data.empty());
  const T** ptr = AllocateROArray2D(data);
  fn(ptr, data.size(), data[0].size());
  FreeROArray2D(ptr, data.size(), data[0].size());
}

#define RUN_ON_RO_ARRAY_2D(ElementType, data, fn)                              \
  ASSERT_NO_FATAL_FAILURE(RunTestOnROArray2D<ElementType>(data, fn));

// ---------------------------------------------------------------------------
// Protected memory: Strings

const char* AllocateROString(const std::string& data);

void FreeROString(const char* ptr, size_t n);

void RunTestOnROString(const std::string& data,
                       const std::function<void(const char* ptr)>& fn);

#define RUN_ON_RO_STRING(data, fn)                                             \
  ASSERT_NO_FATAL_FAILURE(RunTestOnROString(data, fn));

// ---------------------------------------------------------------------------
// Misc

#define TYPE_IS(value, type) (std::is_same_v<decltype(value), type>)

template<typename T>
bool IsConst(T&) {
  return false;
}

template<typename T>
bool IsConst(T const&) {
  return true;
}

template<typename T>
struct Wrapper {
  T value;
  explicit Wrapper(T value) : value(std::move(value)) {}
  Wrapper() = default;
};

template<typename T>
std::string ToString(const std::vector<T>& a) {
  std::stringstream ss;
  ss << "{";
  for (size_t i = 0; i < a.size(); ++i) {
    if (i > 0) {
      ss << ", ";
    }
    ss << a[i];
  }
  ss << "}";
  return ss.str();
}

template<typename T>
std::string ToString2d(const std::vector<std::vector<T>>& a) {
  std::stringstream ss;
  ss << "{";
  for (size_t i = 0; i < a.size(); ++i) {
    if (i > 0) {
      ss << ",\n ";
    }
    ss << ToString(a[i]);
  }
  ss << "}";
  return ss.str();
}

int64_t GetByModule(int64_t x, int64_t m);

template<typename T>
std::vector<T> Unique(const std::vector<T>& values) {
  std::vector<T> result;
  std::set<T> result_set;
  for (const T& element : values) {
    if (result_set.find(element) == result_set.end()) {
      result.push_back(element);
      result_set.insert(element);
    }
  }
  return result;
}

template<typename T>
std::vector<T> Sorted(const std::vector<T>& values) {
  std::vector<T> result = values;
  std::sort(result.begin(), result.end());
  return result;
}

template<typename T>
std::vector<T> Sequence(int size, T first) {
  std::vector<T> result;
  result.reserve(size);
  while (result.size() < size) {
    result.push_back(first++);
  }
  return result;
}

#ifdef __linux__
#define __builtin_smulll_overflow __builtin_smull_overflow
#define __builtin_saddll_overflow __builtin_saddl_overflow
#endif

double RelativeDifference(double value, double answer);

#define ASSERT_NEAR_REL(value, answer, eps)                                    \
    ASSERT_LE(RelativeDifference(value, answer), 2. * eps)                     \
      << "Value = " << value << ", answer = " << answer << '\n'

// ---------------------------------------------------------------------------
// TEST() macro extension

#define SAFE_TEST_A(SuitName, CaseName, timeout_millis, iterations, seed)      \
  void SuitName##CaseName##Body();                                             \
  TEST(SuitName, CaseName) {                                                   \
    TestSuccessTracker tracker;                                                \
    SetRand64Seed(seed);                                                       \
    ASSERT_NOT_INFINITE_LOOP(                                                  \
        timeout_millis, { SuitName##CaseName##Body(); });                      \
    for (int iter = 0; iter < iterations; ++iter ) {                           \
      SetRand64Seed(seed);                                                     \
      ASSERT_NO_FATAL_FAILURE(SuitName##CaseName##Body());                     \
    }                                                                          \
  }                                                                            \
  void SuitName##CaseName##Body()

#define SAFE_TEST(SuitName, CaseName)                                          \
  SAFE_TEST_A(SuitName, CaseName, 30'000, 2, 12345678)

#define ASM_TEST_A(SuitName, CaseName, timeout_millis, iters, seed)            \
  void SuitName##CaseName##TestFn(decltype((Asm##SuitName)) SuitName);         \
  SAFE_TEST_A(SuitName, CaseName##_Regular, timeout_millis, iters, seed) {     \
    SuitName##CaseName##TestFn(Asm##SuitName);                                 \
  }                                                                            \
  SAFE_TEST_A(SuitName, CaseName##_Wrapped, timeout_millis, iters, seed) {     \
    SuitName##CaseName##TestFn(SuitName##Wrapper);                             \
  }                                                                            \
  void SuitName##CaseName##TestFn(decltype((Asm##SuitName)) SuitName)

#define ASM_TEST(SuitName, CaseName)                                           \
  ASM_TEST_A(SuitName, CaseName, 30'000, 3, 12345678)

// Shorter form of the gTest macros
// If any assertions are done inside of a function other than the test body,
// the call of that function must be wrapped into this macro, otherwise
// the failure won't be caught!
#define RUN_TEST_FN(Test) ASSERT_NO_FATAL_FAILURE(Test)

#endif  // UTILS_H
