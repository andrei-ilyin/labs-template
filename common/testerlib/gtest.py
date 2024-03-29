# Copyright (c) 2019-2022 Andrei Ilyin. All rights reserved.
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

import os

from collections import defaultdict
from subprocess import check_output
from tempfile import TemporaryDirectory
from timeit import default_timer as timer

from base import *
from binary_wrapper import BinaryWrapper, maybe_add_exe_extension


class GoogleTestRunner(TestRunner):
    def __init__(self, test_binary_path, suitcase_to_tests, tests_order,
                 dry_run, editions, heavy_tests_editions, runs_count,
                 check_token):
        self._binary_wrappers = [
            BinaryWrapper(test_binary_path + edition, dry_run)
            for edition in editions
        ]
        self._heavy_tests_binary_wrappers = [
            BinaryWrapper(test_binary_path + edition, dry_run)
            for edition in heavy_tests_editions
        ]
        self._suitcase_to_tests = suitcase_to_tests
        self._tests_order = tests_order
        self._runs_count = runs_count
        self._check_token = check_token and not dry_run
        self._heavy_tests = []

    # Mark the test to run only on heavy_tests_editions of the binary
    def mark_heavy_test(self, full_test_name):
        self._heavy_tests.append(full_test_name)

    # Mark the tests in a suit to run only on heavy_tests_editions of the binary
    def mark_heavy_suit(self, suit_name):
        for test_name in self._suitcase_to_tests[suit_name]:
            self.mark_heavy_test(suit_name + '.' + test_name)

    def run(self, description: TestDescription):
        full_test_name = description.suit_name + '.' + description.test_name

        if full_test_name in self._heavy_tests:
            wrappers = self._heavy_tests_binary_wrappers
        else:
            wrappers = self._binary_wrappers

        times_sec = []
        for wrapper in wrappers:
            with TemporaryDirectory(dir=os.curdir) as tmp:
                GTEST_TOKEN_FILENAME = \
                    os.path.join(tmp, 'ANTI_CHEAT_TOKEN_FILENAME')
                GTEST_TOKEN_SECRET = \
                    'ANTI_CHEAT_TOKEN_SECRET'

                for run_id in range(self._runs_count):
                    start_time = timer()
                    verdict = wrapper.run(
                        ["--gtest_filter=" + full_test_name],
                        time_limit_sec=description.resource_limits.time_sec,
                        memory_limit_kb=description.resource_limits.memory_kb,
                        cwd=tmp
                    )
                    finish_time = timer()
                    times_sec.append(finish_time - start_time)

                    if verdict != Verdict.ACCEPTED:
                        return TestResult(verdict, 0, max(times_sec))

                    if self._check_token:
                        if not os.path.exists(GTEST_TOKEN_FILENAME):
                            raise PermissionError('Token file not found!')
                        with open(GTEST_TOKEN_FILENAME, 'r') as f:
                            if f.read().strip() != GTEST_TOKEN_SECRET:
                                raise PermissionError('Token value is wrong!')

        return TestResult(Verdict.ACCEPTED, description.max_score,
                          max(times_sec))

    def get_tests(self):
        result = []
        for (suit_name, test_name) in self._tests_order:
            result.append(Test(
                TestDescription(
                    suit_name=suit_name,
                    test_name=test_name
                ),
                runner=self
            ))
        return result


def prepare_google_test_runner(
        test_binary_path, dry_run, editions=('',), heavy_tests_editions=None,
        runs_count=3):
    sample_binary_path = maybe_add_exe_extension(test_binary_path + editions[0])
    if not os.path.exists(sample_binary_path):
        raise FileNotFoundError(
            'Cannot find binary executable ' + sample_binary_path)

    raw_tests_list = check_output(
        [sample_binary_path, "--gtest_list_tests"]
    ).decode().split('\n')

    suitcase_to_tests = defaultdict(list)
    tests_order = []
    current_tests_suitcase = ''
    for line in raw_tests_list:
        line = line.strip()
        if len(line) == 0 or line.startswith("Running main()"):
            pass
        elif line[-1] == '.':
            current_tests_suitcase = line[:-1]
        else:
            tests_order.append((current_tests_suitcase, line))
            suitcase_to_tests[current_tests_suitcase].append(line)

    if heavy_tests_editions is None:
        heavy_tests_editions = editions

    return GoogleTestRunner(
        test_binary_path, suitcase_to_tests, tests_order, dry_run, editions,
        heavy_tests_editions, runs_count, check_token=True
    )
