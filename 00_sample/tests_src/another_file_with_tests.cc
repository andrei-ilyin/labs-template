#include "gmock/gmock.h"
#include "gtest/gtest.h"
#include "utils/utils.h"

// ---------------------------------------------------------

#include "solution_src/file.h"

int SomeFunc(int x);

// ---------------------------------------------------------

namespace {

SAFE_TEST(Bar, Test) {
  Bar<int> bar = {123};
  ASSERT_EQ(bar.field, 123);
}

SAFE_TEST(SomeFunc, Test) {
  ASSERT_EQ(SomeFunc(123), 123 * 42);
}

} // anonymous namespace
