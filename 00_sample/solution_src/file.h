#ifndef FILE_H_
#define FILE_H_

class Foo {
 public:
  explicit Foo(int value);
  void IncValue();
  int GetValue() const;
 private:
  int value_;
};

template<typename T>
struct Bar {
  T field = -1;
};

#endif  // FILE_H_
