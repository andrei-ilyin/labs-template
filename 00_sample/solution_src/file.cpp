#include "file.h"

Foo::Foo(int value) : value_(value) {}

void Foo::IncValue() {
  ++value_;
}

int Foo::GetValue() const {
  return value_;
}
