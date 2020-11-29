#include "gmock/gmock.h"
#include "gtest/gtest.h"
#include "utils/utils.h"

// ---------------------------------------------------------

#include "solution_src/file.h"

// ---------------------------------------------------------

extern bool kSuccessFlag;

namespace {

SAFE_TEST(Samples, Test1) {
  ASSERT_TRUE(true);
}

SAFE_TEST(Samples, Test2) {
  if (!kSuccessFlag) {
    ASSERT_TRUE(false);
  }
}

SAFE_TEST(Samples, Test3) {
  ASSERT_TRUE(true);
}

SAFE_TEST(YetAnotherPrivateGroup, Test1) {
  ASSERT_TRUE(true);
}

SAFE_TEST(YetAnotherPrivateGroup, Test2) {
  if (!kSuccessFlag) {
    ASSERT_TRUE(false);
  }
}

SAFE_TEST(YetAnotherPrivateGroup, AnotherTest3) {
  ASSERT_TRUE(true);
}

SAFE_TEST(Foo, CtorAndGetter) {
  Foo foo(4242);
  ASSERT_EQ(foo.GetValue(), 4242);
}

SAFE_TEST(Foo, Inc) {
  Foo foo(4242);
  ASSERT_EQ(foo.GetValue(), 4242);
  foo.IncValue();
  ASSERT_EQ(foo.GetValue(), 4243);
  foo.IncValue();
  ASSERT_EQ(foo.GetValue(), 4244);
}

SAFE_TEST(Foo, Failed) {
  if (!kSuccessFlag) {
    ASSERT_TRUE(false);
  }
}

} // anonymous namespace
