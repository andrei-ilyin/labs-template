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

import os
from collections import defaultdict
from subprocess import check_output
from tempfile import TemporaryDirectory

from binary_wrapper import BinaryWrapper, maybe_add_exe_extension


class GTestBinaryWrapper:
    def __init__(self, test_binary_path, suitcase_to_tests, dry_run,
                 editions, runs_count, check_token):
        self._binary_wrappers = [
            BinaryWrapper(test_binary_path + edition, dry_run)
            for edition in editions
        ]
        self._suitcase_to_tests = suitcase_to_tests
        self._runs_count = runs_count
        self._check_token = check_token and not dry_run

    def run_suitcase(self, suitcase):
        if suitcase not in self._suitcase_to_tests:
            raise LookupError("Can't find test suitcase " + suitcase)

        result = True
        for test in self._suitcase_to_tests[suitcase]:
            result = result and self.run_test(suitcase, test)
        return result

    def run_test(self, suitcase, test):
        for wrapper in self._binary_wrappers:
            with TemporaryDirectory(dir=os.curdir) as tmp:
                GTEST_TOKEN_FILENAME = \
                    os.path.join(tmp, 'ANTI_CHEAT_TOKEN_FILENAME')
                GTEST_TOKEN_SECRET = \
                    'ANTI_CHEAT_TOKEN_SECRET'

                for run_id in range(self._runs_count):
                    if not wrapper.run(
                            ["--gtest_filter=" + suitcase + '.' + test],
                            cwd=tmp):
                        return False

                    if self._check_token:
                        if not os.path.exists(GTEST_TOKEN_FILENAME):
                            raise PermissionError('Token file not found!')
                        with open(GTEST_TOKEN_FILENAME, 'r') as f:
                            if f.read().strip() != GTEST_TOKEN_SECRET:
                                raise PermissionError('Token value is wrong!')

                return True

    def get_test_names(self):
        return self._suitcase_to_tests


def prepare_gtest_binary_wrapper(
        test_binary_path, dry_run, editions=('',), runs_count=3):
    sample_binary_path = maybe_add_exe_extension(test_binary_path + editions[0])
    if not os.path.exists(sample_binary_path):
        raise FileNotFoundError(
            'Cannot find binary executable ' + sample_binary_path)

    raw_tests_list = check_output(
        [sample_binary_path, "--gtest_list_tests"]
    ).decode().split('\n')

    suitcase_to_tests = defaultdict(list)
    current_tests_suitcase = ''
    for line in raw_tests_list:
        line = line.strip()
        if len(line) == 0 or line.startswith("Running main()"):
            pass
        elif line[-1] == '.':
            current_tests_suitcase = line[:-1]
        else:
            suitcase_to_tests[current_tests_suitcase].append(line)

    return GTestBinaryWrapper(
        test_binary_path, suitcase_to_tests, dry_run, editions, runs_count,
        check_token=True)
