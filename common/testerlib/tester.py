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

from sys import stdout

from base import *
from interface import TestingSystemInterface


class Tester:
    def __init__(self, overall_tl_sec):
        self._public_tests = []
        self._private_tests = []
        self._aggregated_suits = set()
        self._overall_tl_sec = overall_tl_sec

    def add_public_test(self, test: Test):
        self._public_tests.append(test)

    def add_private_test(self, test: Test):
        self._private_tests.append(test)

    def run(self, test_system_interface: TestingSystemInterface,
            verbose=False, print_report_to_stderr=True):
        try:
            # Get mode
            testing_mode = test_system_interface.get_test_mode()
            if testing_mode == TestingSystemInterface.PUBLIC_TESTS_RUN:
                tests_list = self._public_tests
            elif testing_mode == TestingSystemInterface.PRIVATE_TESTS_RUN:
                tests_list = self._private_tests
            elif testing_mode == TestingSystemInterface.ALL_TESTS_RUN:
                tests_list = self._public_tests + self._private_tests
            else:
                raise NotImplementedError('testing mode not supported')

            # Execute the tests
            self._run_tests(tests_list, verbose)

            # Prepare test groups
            test_groups = dict()
            for test in tests_list:
                suit_name = test.description.suit_name
                if test.description.exclude_from_aggregation:
                    test_name = test.description.test_name
                    group = TestGroup(suit_name, test_name)
                    group.description = test.description
                    group.result = test.result
                    group.tests.append(test)
                    if test.result.verdict == Verdict.ACCEPTED:
                        group.passed_tests_count = 1
                    test_groups[test.description.full_name()] = group
                else:
                    group_name = suit_name + '.*'
                    if group_name not in test_groups:
                        test_groups[group_name] = TestGroup(suit_name, '*')
                    test_groups[group_name].update_with_test(test)

            # Generate full report
            report = TestingReport()
            for group_name in test_groups:
                report.update_with_group(test_groups[group_name])

            # Send report to the system
            test_system_interface.write_report(report, print_report_to_stderr)

        except TimeoutError as e:
            report = TestingReport()
            report.result.verdict = Verdict.TIME_LIMIT_EXCEEDED
            report.result.time_sec = self._overall_tl_sec
            report.general_comment = 'TLE: ' + str(e)
            test_system_interface.write_report(report, print_report_to_stderr)

        except Exception as e:
            report = TestingReport()
            report.result.verdict = Verdict.CHECK_FAILED
            report.general_comment = 'CF: ' + str(e)
            test_system_interface.write_report(report, print_report_to_stderr)

    def _run_tests(self, tests_list, verbose):
        overall_time_sec = 0
        for test in tests_list:
            if test.result is not None:
                if verbose:
                    print("-- skipping '%s.%s' (dependency failed)" % (
                        test.description.suit_name,
                        test.description.test_name))
                    stdout.flush()
                continue

            if verbose:
                print("-- running '%s.%s'" % (
                    test.description.suit_name, test.description.test_name))
                stdout.flush()

            test.result = test.runner.run(test.description)

            overall_time_sec += test.result.time_sec
            if overall_time_sec > self._overall_tl_sec:
                raise TimeoutError(
                    'General time limit exceeded. Testing aborted.')

            if test.result.verdict != Verdict.ACCEPTED:
                for dependent_test in test.description.dependencies:
                    dependent_test.result = TestResult(
                        Verdict.DEPENDENCY_FAILED, 0, 0)
