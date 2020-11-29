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
from sys import stderr, stdout

from base import *


def _eprint(*args, **kwargs):
    print(*args, file=stderr, **kwargs)


def _verdict_to_log_str(verdict: Verdict):
    if verdict == Verdict.CHECK_FAILED:
        return 'SYS_FL'
    elif verdict == Verdict.ACCEPTED:
        return '  OK  '
    elif verdict == Verdict.FAILED:
        return ' FAIL '
    elif verdict == Verdict.DEPENDENCY_FAILED:
        return 'DEP_FL'
    elif verdict == Verdict.TIME_LIMIT_EXCEEDED:
        return ' TLE  '
    elif verdict == Verdict.MEMORY_LIMIT_EXCEEDED:
        return ' MLE  '
    else:
        return '? NA ?'


def _verdict_to_irunner_str(verdict: Verdict):
    if verdict == Verdict.ACCEPTED:
        return 'ACCEPTED'
    else:
        return 'FAILED'

    # TODO: Handle various verdicts in iRunner
    # if verdict == Verdict.ACCEPTED or \
    #         verdict == Verdict.FAILED or \
    #         verdict == Verdict.TIME_LIMIT_EXCEEDED or \
    #         verdict == Verdict.MEMORY_LIMIT_EXCEEDED:
    #     return str(verdict)
    # else:
    #     return 'CHECK_FAILED'


def _to_log_line(test, print_time=False):
    result_str = '[%s] (score: %s / %s)' % (
        _verdict_to_log_str(test.result.verdict),
        str(round(test.result.score, 3)),
        str(round(test.description.max_score, 3))
    )
    result_str = ('%-35s' % result_str) + test.description.full_name()

    if print_time:
        result_str += '    (time: %.3f s)' % test.result.time_sec

    return result_str


def _group_public_feedback(group: TestGroup):
    return '%s [score: %s / %s]' % (
        group.description.full_name(),
        str(round(group.result.score, 3)),
        str(round(group.description.max_score, 3)),
    )


def _group_judges_feedback(group: TestGroup):
    tests = []
    for test in group.tests:
        tests.append(_to_log_line(test, print_time=True))
    return '\n'.join(tests)


class TestingSystemInterface:
    PUBLIC_TESTS_RUN = 'public'
    PRIVATE_TESTS_RUN = 'private'
    ALL_TESTS_RUN = 'all'

    def get_test_mode(self):
        raise NotImplementedError("get_test_mode")

    def write_report(self, report: TestingReport, print_stderr_report):
        raise NotImplementedError("write_system_report")

    def _print_stderr_report(self, report: TestingReport, print_time=False):
        for group in report.groups:
            _eprint(_to_log_line(group, print_time))
        if report.general_comment is not None:
            _eprint(report.general_comment)
        _eprint("Passed %s out of %s tests" % (
            str(report.passed_tests_count), str(report.tests_count)))
        if print_time:
            _eprint("Total time: %.3f s" % report.result.time_sec)
        _eprint("Total score: %s out of %s" % (
            str(round(report.result.score, 3)),
            str(round(report.max_score, 3))))
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

    def write_report(self, report: TestingReport, print_stderr_report):
        if print_stderr_report:
            self._print_stderr_report(report)
        # for group in report.groups:
        #     print(_group_judges_feedback(group) + '\n')
        with open(self._output_filename, "w") as f:
            f.write(self._output_secret + "\n"
                    + str(round(report.result.score, 3)))


class IRunnerInterface(TestingSystemInterface):
    def __init__(self, report_file):
        self._report_file = report_file

    def get_test_mode(self):
        return self.ALL_TESTS_RUN

    def write_report(self, report: TestingReport, print_stderr_report):
        if print_stderr_report:
            self._print_stderr_report(report, print_time=True)
        self._write_json(report)

    def _group_json(self, verdict: Verdict, score=0, max_score=0, time_ms=0,
                    time_limit_ms=0, checker_comment='', stderr='', stdout='',
                    answer=''):
        return {
            'verdict': (verdict == Verdict.ACCEPTED),
            # 'verdict': _verdict_to_irunner_str(verdict),
            'score': score,
            'max_score': max_score,
            'time_ms': 0,
            'time_limit_ms': 0,
            # 'time_ms': time_ms,
            # 'time_limit_ms': time_limit_ms,
            'comment': checker_comment,
            'output': answer,
            'stdout': stdout,
            'stderr': stderr,
        }

    def _write_json(self, report: TestingReport):
        tests = []
        if report.general_comment is not None:
            tests.append(self._group_json(
                report.result, checker_comment=report.general_comment))

        for group in report.groups:
            tests.append(self._group_json(
                group.result.verdict,
                score=round(group.result.score),
                max_score=round(group.description.max_score),
                time_ms=group.result.time_sec * 1000,
                time_limit_ms=group.description.resource_limits.time_sec * 1000,
                checker_comment=_group_public_feedback(group),
                answer=_group_judges_feedback(group),
            ))

        with open(self._report_file, 'w') as outfile:
            dump({
                'verdict': _verdict_to_irunner_str(report.result.verdict),
                'score': round(report.result.score),
                'max_score': round(report.max_score),
                'tests': tests,
            }, outfile)
