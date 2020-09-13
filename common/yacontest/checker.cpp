#include <fstream>
#include <iostream>
#include <string>

using namespace std;

int main(int argc, char *argv[]) {
  ifstream inf(argv[1]);
  ifstream ouf(argv[2]);
  ifstream ans(argv[3]);

  if (argc > 4) {
    freopen(argv[4], "w", stdout);
  }

  std::string p_key, j_key;
  ouf >> p_key;
  ans >> j_key;
  if (p_key != j_key) {
    cout << "Potential security violation - incorrect secret." << endl;
    return 5; // WA
  }

  double p_score;
  ouf >> p_score;

  std::string testcase;
  inf >> testcase;
  if (testcase == "public") {
    p_score = 1;
  } else if (p_score == 0) {
    cout << "points  " << p_score << endl;
    return 1; // WA
  }

  cout << "points " << p_score << endl;
  return 0; // OK
}
