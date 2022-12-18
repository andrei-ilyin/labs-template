#!/usr/bin/env python3

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

import argparse
import os

from interface import YandexContestInterface, IRunnerInterface, LocalInterface
from tester_config import configure

YANDEX_CONTEST_MODE = 'yandex-contest'
IRUNNER_MODE = 'irunner'
LOCAL_MODE = 'local'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--build-dir',
                        default=os.curdir,
                        help='Path to the directory with executables.')
    parser.add_argument('--mode',
                        default=IRUNNER_MODE,
                        choices=[YANDEX_CONTEST_MODE, IRUNNER_MODE, LOCAL_MODE])
    parser.add_argument('--dry-run',
                        default=False,
                        help='If true, doesn\'t actually execute the tests.',
                        action='store_true')
    parser.add_argument('--disable-aggregation',
                        default=False,
                        help='If enabled, some test details are hidden.'
                             ' Exact configuration for this feature is defined'
                             ' in \'tester_config\' script.',
                        action='store_true')
    parser.add_argument('--print-report-to-stderr',
                        default=False,
                        help='If specified, prints final results to stderr.'
                             ' Always enabled in Yandex.Contest mode.',
                        action='store_true')
    parser.add_argument('--verbose-testing',
                        default=False,
                        help='If specified, continuously prints information '
                             ' about testing progress to stdout.',
                        action='store_true')
    parser.add_argument('--print-test-config',
                        default=False,
                        help='Extends verbose info with config (TL/ML/etc.).',
                        action='store_true')
    parser.add_argument('--time-limit-debug',
                        default=False,
                        help='If enabled, TLE will not cause test failure, but'
                             ' there will be a warning printed if exec time is'
                             ' less than 1/4 of the specified TL.',
                        action='store_true')
    parser.add_argument('--irunner-report-json')
    args = parser.parse_args()

    if args.mode == YANDEX_CONTEST_MODE:
        test_system_interface = YandexContestInterface()
    elif args.mode == IRUNNER_MODE:
        test_system_interface = IRunnerInterface(args.irunner_report_json)
    else:
        test_system_interface = LocalInterface()

    config = configure(args.build_dir, args.dry_run)
    tester = config.create_tester(
        enable_aggregation=not args.disable_aggregation,
        time_limit_debug_mode=args.time_limit_debug)
    tester.run(test_system_interface, verbose=args.verbose_testing,
               print_report_to_stderr=args.print_report_to_stderr,
               print_test_config=args.print_test_config)
