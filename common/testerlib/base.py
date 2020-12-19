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

from enum import Enum


class Verdict(Enum):
    CHECK_FAILED = 0,
    ACCEPTED = 1,
    FAILED = 2,
    DEPENDENCY_FAILED = 3,
    TIME_LIMIT_EXCEEDED = 4,
    MEMORY_LIMIT_EXCEEDED = 5


class TestType(Enum):
    UNUSED = 0,
    IGNORED = 1,
    PUBLIC = 2,
    PRIVATE = 3,


class ResourceLimits:
    def __init__(self, time_sec, memory_kb):
        self.time_sec = time_sec
        self.memory_kb = memory_kb


class TestDescription:
    def __init__(self, suit_name, test_name, max_score=0,
                 type: TestType = TestType.UNUSED,
                 resource_limits: ResourceLimits = None,
                 exclude_from_aggregation=False):
        self.suit_name = suit_name
        self.test_name = test_name
        self.max_score = max_score
        self.type = type
        self.dependencies = []
        self.resource_limits = resource_limits
        self.exclude_from_aggregation = exclude_from_aggregation

    def full_name(self):
        return self.suit_name + '.' + self.test_name


class TestResult:
    def __init__(self, verdict, score, time_sec):
        self.verdict = verdict
        self.score = score
        self.time_sec = time_sec


class TestRunner:
    # returns TestResult
    def run(self, description: TestDescription):
        raise NotImplementedError('TestRunner.run(...)')

    # returns list of Test
    def get_tests(self):
        raise NotImplementedError('TestRunner.get_tests()')


class Test:
    def __init__(self, description: TestDescription, runner: TestRunner,
                 result: TestResult = None):
        self.description = description
        self.runner = runner
        self.result = result

    def __str__(self):
        return self.description.full_name()


class TestGroup:
    def __init__(self, suit_name, test_name):
        self.description = TestDescription(
            suit_name, test_name, resource_limits=ResourceLimits(0, None))
        self.result = TestResult(Verdict.ACCEPTED, 0, 0)
        self.tests = []
        self.passed_tests_count = 0

    def update_with_test(self, test: Test):
        self.tests.append(test)

        self.description.resource_limits.time_sec += \
            test.description.resource_limits.time_sec
        self.description.max_score += test.description.max_score

        self.result.score += test.result.score
        self.result.time_sec += test.result.time_sec
        if test.result.verdict == Verdict.ACCEPTED:
            self.passed_tests_count += 1
        else:
            self.result.verdict = Verdict.FAILED


class TestingReport:
    def __init__(self):
        self.max_score = 0
        self.result = TestResult(Verdict.FAILED, 0, 0)
        self.groups = []
        self.tests_count = 0
        self.passed_tests_count = 0
        self.general_comment = None

    def update_with_group(self, group: TestGroup):
        self.max_score += group.description.max_score

        self.result.score += group.result.score
        self.result.time_sec += group.result.time_sec
        if group.result.score > 0:
            self.result.verdict = Verdict.ACCEPTED

        self.groups.append(group)
        self.tests_count += len(group.tests)
        self.passed_tests_count += group.passed_tests_count
