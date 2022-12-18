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

import re

from base import *
from tester import Tester


class Configurator:
    def __init__(self, overall_tl_sec=600, default_time_limit_sec=180,
                 default_memory_limit_kb=None):
        self._tests_order = []
        self._full_name_to_test = {}
        self._suits = set()
        self._standalone_tests = []
        self._overall_tl_sec = overall_tl_sec
        self._default_time_limit_sec = default_time_limit_sec
        self._default_memory_limit_kb = default_memory_limit_kb

    def load_runner(self, runner: TestRunner):
        for test in runner.get_tests():
            test_full_name = test.description.full_name()
            if test_full_name in self._full_name_to_test:
                print("ERROR: Test '%s' loaded multiple times!" % test)
            else:
                test.description.resource_limits = ResourceLimits(
                    self._default_time_limit_sec,
                    self._default_memory_limit_kb
                )
                self._tests_order.append(test_full_name)
                self._full_name_to_test[test_full_name] = test
                self._suits.add(test.description.suit_name)

    def override_time_limit(self, regex_filter, time_limit_sec):
        for test_full_name in self._tests_order:
            if re.match(regex_filter, test_full_name):
                self._full_name_to_test[test_full_name]. \
                    description.resource_limits.time_sec = time_limit_sec

    def override_memory_limit(self, regex_filter, memory_limit_kb):
        for test_full_name in self._tests_order:
            if re.match(regex_filter, test_full_name):
                self._full_name_to_test[test_full_name]. \
                    description.resource_limits.memory_kb = memory_limit_kb

    def _process_group(self, regex_filter, group_score, group_type):
        tests = []
        for test_name in self._tests_order:
            if re.match(regex_filter, test_name):
                tests.append(self._full_name_to_test[test_name])

        if len(tests) == 0:
            print("ERROR: No tests match regex '%s'" % regex_filter)
            return

        if group_type == TestType.IGNORED:
            for test in tests:
                if test.description.type == TestType.PUBLIC or \
                        test.description.type == TestType.PRIVATE:
                    print("ERROR: Test '%s' will not be ignored!" % test)
                else:
                    test.description.type = TestType.IGNORED
            return

        if group_type == TestType.PUBLIC:
            for test in tests:
                if test.description.type == TestType.PRIVATE:
                    print("ERROR: Scored test '%s' cannot be redefined as"
                          " public! Define public tests prior to private."
                          % test)
                elif test.description.type == TestType.IGNORED:
                    print("ERROR: Test '%s' will not be ignored!" % test)
                else:
                    test.description.type = TestType.PUBLIC
            return

        validated_tests = []
        for test in tests:
            if test.description.type == TestType.IGNORED:
                print("ERROR: Test '%s' will not be ignored!" % test)
            elif test.description.type == TestType.PRIVATE:
                print("ERROR: Test '%s' matches multiple scored filters!"
                      % test)
            elif test.description.type == TestType.UNUSED:
                validated_tests.append(test)
            else:
                # If the test was previously defined as 'public', it will be
                # excluded from further 'private' regex matches without
                # warning. This is used for testsets where public tests are
                # part of suits with scored tests.
                pass

        if len(validated_tests) == 0:
            print("ERROR: No tests match regex '%s'" % regex_filter)
            return

        single_test_score = group_score / len(validated_tests)
        for test in validated_tests:
            test.description.max_score = single_test_score
            test.description.type = TestType.PRIVATE

    def add_public_suit(self, suit_name):
        self._process_group(suit_name + '\\..*', 0, TestType.PUBLIC)

    def add_private_suit(self, suit_name, score):
        self._process_group(suit_name + '\\..*', score, TestType.PRIVATE)

    def add_public_test(self, suit_name, test_name):
        self._process_group(
            suit_name + '\\.' + test_name + '$', 0, TestType.PUBLIC)

    def add_private_test(self, suit_name, test_name, score):
        self._process_group(
            suit_name + '\\.' + test_name + '$', score, TestType.PRIVATE)

    def add_public_group(self, regex_filter):
        self._process_group(regex_filter, 0, TestType.PUBLIC)

    def add_private_group(self, regex_filter, score):
        self._process_group(regex_filter, score, TestType.PRIVATE)

    def skip_group(self, regex_filter):
        self._process_group(regex_filter, 0, TestType.IGNORED)

    def force_skip_group(self, regex_filter, reverse_filter=False):
        for test_name in self._tests_order:
            if (re.match(regex_filter, test_name) is not None) ^ (reverse_filter):
                self._full_name_to_test[test_name].description.type = TestType.IGNORED

    def mark_standalone_tests(self, regex_filter):
        self._standalone_tests.append(regex_filter)

    def add_dependency(self, target_tests_filter, required_tests_filter):
        required_tests = []
        for test_full_name in self._tests_order:
            if re.match(target_tests_filter, test_full_name):
                required_tests.append(self._full_name_to_test[test_full_name])

        for test_full_name in self._tests_order:
            if re.match(required_tests_filter, test_full_name):
                self._full_name_to_test[
                    test_full_name].description.dependencies += required_tests

    def normalize_scores(self, total_score):
        scores_sum = 0
        for test_full_name in self._tests_order:
            scores_sum += self._full_name_to_test[
                test_full_name].description.max_score

        scale = total_score / scores_sum
        for test_full_name in self._tests_order:
            self._full_name_to_test[
                test_full_name].description.max_score *= scale

    def create_tester(self, enable_aggregation, time_limit_debug_mode):
        tester = Tester(overall_tl_sec=self._overall_tl_sec,
                        enable_time_limit_debug_mode=time_limit_debug_mode)

        for test_full_name in self._tests_order:
            test = self._full_name_to_test[test_full_name]

            if not enable_aggregation:
                test.description.exclude_from_aggregation = True
            else:
                for filter_re in self._standalone_tests:
                    if re.match(filter_re, test_full_name):
                        test.description.exclude_from_aggregation = True

            if test.description.type == TestType.UNUSED:
                print("WARNING: Test '%s' has not been used" %
                      test.description.full_name())
            elif test.description.type == TestType.PUBLIC:
                tester.add_public_test(test)
            elif test.description.type == TestType.PRIVATE:
                tester.add_private_test(test)

        return tester
