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

import re
from sys import stdout
from collections import defaultdict

from interface import TestingSystemInterface, TestResult


class Test:
    def __init__(self, suit_name, test_name, score, runner_fn):
        self.suite_name = suit_name
        self.test_name = test_name
        self.score = score
        self.detailed_report = False
        self.runner_fn = runner_fn
        self.dependencies = []
        self.is_passed = False


class Tester:
    def __init__(self):
        self._public_tests = []
        self._private_tests = []
        self._aggregated_suits = set()

    def add_public_test(self, test: Test):
        test.detailed_report = True
        self._public_tests.append(test)

    def add_private_test(self, test: Test):
        test.detailed_report = False
        self._private_tests.append(test)

    def aggregate_suit(self, suit_name):
        self._aggregated_suits.add(suit_name)

    def run(self, test_system_interface: TestingSystemInterface,
            verbose=False, print_report_to_stderr=True):
        try:
            testing_mode = test_system_interface.get_test_mode()
            if testing_mode == TestingSystemInterface.PUBLIC_TESTS_RUN:
                tests_list = self._public_tests
            elif testing_mode == TestingSystemInterface.PRIVATE_TESTS_RUN:
                tests_list = self._private_tests
            elif testing_mode == TestingSystemInterface.ALL_TESTS_RUN:
                tests_list = self._public_tests + self._private_tests
            else:
                raise NotImplementedError('testing mode not supported')

            self._test(tests_list, verbose)

            aggregated_suit_to_gained_score = defaultdict(int)
            aggregated_suit_to_max_score = defaultdict(int)

            total_score = 0
            total_max_score = 0

            total_passed = 0
            total_max_passed = 0

            results = []
            for test in tests_list:
                suit_name = test.suite_name
                test_name = test.test_name
                test_score = test.score

                total_max_score += test_score
                total_max_passed += 1

                gained_score = test_score if test.is_passed else 0
                total_score += gained_score
                if test.is_passed:
                    total_passed += 1

                if not test.detailed_report and \
                        (suit_name in self._aggregated_suits):
                    aggregated_suit_to_max_score[suit_name] += test_score
                    aggregated_suit_to_gained_score[suit_name] += gained_score
                else:
                    results.append(TestResult(
                        suit_name + '.' + test_name,
                        test.is_passed,
                        test.score if test.is_passed else 0,
                        test.score
                    ))

            for suit in sorted(aggregated_suit_to_gained_score.keys()):
                gained_score = aggregated_suit_to_gained_score[suit]
                max_score = aggregated_suit_to_max_score[suit]
                results.append(TestResult(
                    suit + '.*',
                    score=gained_score,
                    max_score=max_score
                ))

            results.sort(key=lambda x: x.title)

            test_system_interface.write_report(
                total_max_score, total_score,
                total_max_passed, total_passed,
                results, print_report_to_stderr
            )

        except Exception as e:
            test_system_interface.report_error(str(e))

    def _test(self, tests_list, verbose):
        for test in tests_list:
            if verbose:
                print("-- running '%s.%s'" % (test.suite_name, test.test_name))
                stdout.flush()
            test.is_passed = test.runner_fn()

        for test in tests_list:
            for dependency in test.dependencies:
                if not dependency.is_passed:
                    test.is_passed = False


class Configurator:
    def __init__(self):
        self._name_to_wrapper = {}
        self._suitcases = set()
        self._scored_test_names = set()
        self._public_test_names = set()
        self._private_tests = []
        self._public_tests = []
        self._detailed_suits = []

    def load_test(self, suite_name, test_name, runner_fn):
        self._suitcases.add(suite_name)
        self._name_to_wrapper[suite_name + '.' + test_name] = Test(
            suite_name, test_name, 0, runner_fn)

    def load_google_binary(self, wrapper):
        def create_runner_fn(suitcase, test):
            def runner_fn():
                return wrapper.run_test(suitcase, test)

            return runner_fn

        suitcase_to_test = wrapper.get_test_names()
        for suitcase in suitcase_to_test.keys():
            for test in suitcase_to_test[suitcase]:
                self.load_test(suitcase, test, create_runner_fn(suitcase, test))

    def process_group(self, regex_filter, group_score, group_type):
        tests = []
        for test in self._name_to_wrapper.keys():
            if re.match(regex_filter, test):
                tests.append(test)

        if len(tests) == 0:
            print("ERROR: No tests match regex '%s'" % regex_filter)
            return

        test_score = group_score / len(tests)
        for test in tests:
            if test in self._scored_test_names:
                print("ERROR: Test '%s' matches multiple scored filters" % test)
                continue
            elif test in self._public_test_names:
                continue

            wrapper = self._name_to_wrapper[test]
            wrapper.score = test_score

            if group_type == 'private':
                self._scored_test_names.add(test)
                self._private_tests.append(wrapper)
            elif group_type == 'public':
                self._public_test_names.add(test)
                self._public_tests.append(wrapper)
            elif group_type == 'disabled':
                self._scored_test_names.add(test)
                pass
            else:
                print("ERROR: Incorrect test type '%s'" % group_type)

    def add_public_suit(self, suit_name):
        self.process_group(suit_name + '\\..*', 0, 'public')

    def add_private_suit(self, suit_name, score):
        self.process_group(suit_name + '\\..*', score, 'private')

    def add_public_test(self, suit_name, test_name):
        self.process_group(suit_name + '\\.' + test_name + '$', 0, 'public')

    def add_private_test(self, suit_name, test_name, score):
        self.process_group(
            suit_name + '\\.' + test_name + '$', score, 'private')

    def add_public_group(self, regex_filter):
        self.process_group(regex_filter, 0, 'public')

    def add_private_group(self, regex_filter, score):
        self.process_group(regex_filter, score, 'private')

    def skip_group(self, regex_filter):
        self.process_group(regex_filter, 0, 'disabled')

    def add_detailed_suits(self, regex_filter):
        self._detailed_suits.append(regex_filter)

    def add_dependency(self, target_tests_filter, required_tests_filter):
        required_tests = []
        for test in self._name_to_wrapper.keys():
            if re.match(required_tests_filter, test):
                required_tests.append(self._name_to_wrapper[test])

        for test in self._name_to_wrapper.keys():
            if re.match(target_tests_filter, test):
                self._name_to_wrapper[test].dependencies += required_tests

    def normalize_scores(self, total_score):
        scores_sum = 0
        for test in self._private_tests:
            scores_sum += test.score

        scale = total_score / scores_sum
        for test in self._private_tests:
            test.score *= scale

    def create_tester(self, enable_aggregation):
        for test in self._name_to_wrapper.keys():
            if (test not in self._scored_test_names) and \
                    (test not in self._public_test_names):
                print("WARNING: Test '%s' has not been used" % test)

        scorer = Tester()

        if enable_aggregation:
            for suitcase in self._suitcases:
                aggregate = True
                for filter_re in self._detailed_suits:
                    if re.match(filter_re, suitcase):
                        aggregate = False
                if aggregate:
                    scorer.aggregate_suit(suitcase)

        for test in self._public_tests:
            scorer.add_public_test(test)

        for test in self._private_tests:
            scorer.add_private_test(test)

        return scorer
