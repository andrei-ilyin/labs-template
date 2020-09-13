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

#include <fstream>

#include "utils.h"

namespace {

uint64_t secret_counter = -1;

}  // anonymous namespace

TestSuccessTracker::TestSuccessTracker() {
#ifndef DISABLE_SUCCESS_TRACKER
  ++secret_counter;
  // std::ofstream fout("ANTI_CHEAT_TOKEN_FILENAME");
  // fout << "__Something_is_still_running__";
#endif  // DISABLE_SUCCESS_TRACKER
}

TestSuccessTracker::~TestSuccessTracker() {
#ifndef DISABLE_SUCCESS_TRACKER
  --secret_counter;
  if (secret_counter == -1) {
    std::ofstream fout("ANTI_CHEAT_TOKEN_FILENAME");
    fout << "ANTI_CHEAT_TOKEN_SECRET";
  }
#endif  // DISABLE_SUCCESS_TRACKER
}

namespace {

std::mt19937_64 random_generator_(12345678);

}  // anonymous namespace

void SetRand64Seed(uint64_t new_seed) {
  random_generator_.seed(new_seed);
}

uint64_t Rand64() {
  return random_generator_();
}

uint64_t URandom64(uint64_t min, uint64_t max) {
  uint64_t range_size = max + 1ll - min;
  return min + static_cast<long long>(Rand64() % range_size);
}

int64_t SRandom64(int64_t min, int64_t max) {
  uint64_t range_size = max + 1ll - min;
  return min + static_cast<long long>(Rand64() % range_size);
}

uint32_t URandom32(uint32_t min, uint32_t max) {
  return URandom64(min, max);
}

int32_t SRandom32(int32_t min, int32_t max) {
  return SRandom64(min, max);
}

std::vector<int32_t> RandomInt32Array(size_t n, int32_t min, int32_t max) {
  std::vector<int32_t> result;
  for (size_t i = 0; i < n; ++i) {
    result.push_back(SRandom32(min, max));
  }
  return result;
}

std::vector<uint32_t> RandomUInt32Array(size_t n, uint32_t min, uint32_t max) {
  std::vector<uint32_t> result;
  for (size_t i = 0; i < n; ++i) {
    result.push_back(URandom32(min, max));
  }
  return result;
}

std::vector<int64_t> RandomInt64Array(size_t n, int64_t min, int64_t max) {
  std::vector<int64_t> result;
  for (size_t i = 0; i < n; ++i) {
    result.push_back(SRandom64(min, max));
  }
  return result;
}

std::vector<uint64_t> RandomUInt64Array(size_t n, uint64_t min, uint64_t max) {
  std::vector<uint64_t> result;
  for (size_t i = 0; i < n; ++i) {
    result.push_back(URandom64(min, max));
  }
  return result;
}

std::string RandomString(size_t n, int64_t min, int64_t max) {
  std::string result;
  for (size_t i = 0; i < n; ++i) {
    int64_t x = min + Rand64() % (max - min + 1);
    result.push_back(static_cast<unsigned char>(x));
  }
  return result;
}

// ---------------------------------------------------------------------------

const char* AllocateROString(const std::string& data) {
  char* result = nullptr;
  size_t bytes_allocated = AllocationSize<char>(data.length() + 1);
  size_t bytes_to_copy = sizeof(char) * (data.length() + 1);

#ifdef __linux__
  result = (char*) mmap(nullptr, bytes_allocated, PROT_READ | PROT_WRITE,
                        MAP_PRIVATE | MAP_ANONYMOUS, 0, 0);
#elif _WIN32
  result = static_cast<char*>(VirtualAlloc(
      nullptr, bytes_allocated, MEM_COMMIT, PAGE_READWRITE));
#endif

  memcpy(result, data.c_str(), bytes_to_copy);
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

void FreeROString(const char* ptr, size_t n) {
#ifdef __linux__
  munmap((void*) ptr, AllocationSize<char>(n));
#elif _WIN32
  VirtualFree((void*) ptr, AllocationSize<char>(n), MEM_DECOMMIT);
#endif
}

void RunTestOnROString(const std::string& data,
                       const std::function<void(const char* ptr)>& fn) {
  const char* ptr = AllocateROString(data);
  fn(ptr);
  FreeROString(ptr, data.length());
}

// ---------------------------------------------------------------------------

int64_t GetByModule(int64_t x, int64_t m) {
  int64_t r = x % m;
  if (r < 0) {
    r += m;
  }
  return r;
}

double RelativeDifference(double value, double answer) {
  // assert(!std::isnan(value) && !std::isinf(value));
  assert(!std::isnan(answer) && !std::isinf(answer));
  double diff = fabs(value - answer);
  if (fabs(answer) > 0) {
    diff /= fabs(answer);
  }
  return diff;
}
