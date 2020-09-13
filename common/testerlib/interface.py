# Copyright (c) 2019-2020 Andrei Ilyin. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#    * Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above
# copyright notice, this list of conditions and the following disclaimer
# in the documentation and/or other materials provided with the
# distribution.
#    * Changes made to the source code must be documented if this code is
# published in a repository/storage with a public access.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from json import dump
from sys import stderr


def _eprint(*args, **kwargs):
    print(*args, file=stderr, **kwargs)


def _to_log_line(test_result):
    if test_result.success:
        verdict = '  OK  '
    else:
        verdict = ' FAIL '

    result_str = '[%s] (score: %s / %s)' % (
        verdict,
        str(round(test_result.score, 3)),
        str(round(test_result.max_score, 3))
    )
    return ('%-35s' % result_str) + test_result.title


class TestResult:
    def __init__(self, title, success=None, score=0, max_score=1):
        if success is None:
            success = (score == max_score)
        self.title = title
        self.success = success
        self.score = score
        self.max_score = max_score


class TestingSystemInterface:
    PUBLIC_TESTS_RUN = 'public'
    PRIVATE_TESTS_RUN = 'private'
    ALL_TESTS_RUN = 'all'

    def get_test_mode(self):
        raise NotImplementedError("get_test_mode")

    def report_error(self, message):
        raise NotImplementedError("report_error")

    def write_report(self, score_max, score_gained,
                     tests_count, tests_passed, detailed_test_results,
                     print_report_to_stderr):
        raise NotImplementedError("write_system_report")

    def _print_stderr_report(self, score_max, score_gained,
                             tests_count, tests_passed, detailed_test_results):
        for result in detailed_test_results:
            _eprint(_to_log_line(result))
        _eprint("Passed %s out of %s tests" % (
            str(tests_passed), str(tests_count)))
        _eprint("Total score: %s out of %s" % (
            str(round(score_gained, 3)), str(round(score_max, 3))))
        stderr.flush()


class YandexContestInterface(TestingSystemInterface):
    def __init__(self,
                 input_filename="INPUT_FILE_NAME",
                 output_filename="OUTPUT_FILE_NAME",
                 public_secrets=("public", "PUBLIC_SECRET_HERE"),
                 private_secrets=("private", "PRIVATE_SECRET_HERE")):
        self._input_filename = input_filename
        self._output_filename = output_filename
        self._public_secret = public_secrets
        self._private_secret = private_secrets
        self._output_secret = ''

    def get_test_mode(self):
        with open(self._input_filename, "r") as f:
            content = f.read().strip()
            if content == self._public_secret[0]:
                self._output_secret = self._public_secret[1]
                return self.PUBLIC_TESTS_RUN
            elif content == self._private_secret[0]:
                self._output_secret = self._private_secret[1]
                return self.PRIVATE_TESTS_RUN
            else:
                raise PermissionError("Wrong input secret!")

    def write_report(self, score_max, score_gained,
                     tests_count, tests_passed, detailed_test_results,
                     print_report_to_stderr):
        self._print_stderr_report(score_max, score_gained,
                                  tests_count, tests_passed,
                                  detailed_test_results)
        with open(self._output_filename, "w") as f:
            f.write(self._output_secret + "\n" + str(round(score_gained, 3)))

    def report_error(self, message):
        _eprint('Error: ' + message)
        stderr.flush()
        with open(self._output_filename, "w") as f:
            f.write(self._output_secret + "\n" + str(0))


class IRunnerInterface(TestingSystemInterface):
    def __init__(self, report_file):
        self._report_file = report_file

    def get_test_mode(self):
        return self.ALL_TESTS_RUN

    def write_report(self, score_max, score_gained,
                     tests_count, tests_passed, detailed_test_results,
                     print_report_to_stderr):
        if print_report_to_stderr:
            self._print_stderr_report(
                score_max, score_gained,
                tests_count, tests_passed, detailed_test_results)
        self._write_json('ACCEPTED', score_gained, score_max,
                         detailed_test_results)

    def report_error(self, message):
        _eprint('Error: ' + message)
        stderr.flush()
        self._write_json('CHECK_FAILED', 0, [])

    @staticmethod
    def _comment(test_result):
        return '%s [score: %s / %s]' % (
            test_result.title,
            str(round(test_result.score, 3)),
            str(round(test_result.max_score, 3)),
        )

    def _write_json(self, verdict, score, max_score, test_results):
        tests = []
        for result in test_results:
            tests.append({
                'verdict': result.success,
                'score': round(result.score),
                'max_score': round(result.max_score),
                'time_ms': 0,
                'time_limit_ms': 0,
                'comment': self._comment(result),
                'output': '',
                'stdout': '',
                'stderr': '',
            })

        with open(self._report_file, 'w') as outfile:
            dump({
                'verdict': verdict,
                'score': round(score),
                'max_score': round(max_score),
                'tests': tests,
            }, outfile)
