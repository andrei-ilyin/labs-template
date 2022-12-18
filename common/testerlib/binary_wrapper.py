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
import platform
import subprocess
import sys
import threading

from tempfile import TemporaryDirectory

from base import Verdict

if sys.version_info[1] >= 3:
    from subprocess import TimeoutExpired
else:
    class TimeoutExpired(Exception):
        pass


def _is_running_on_windows():
    return platform.system() == 'Windows'


def maybe_add_exe_extension(path):
    if _is_running_on_windows():
        path += '.exe'
    return path


class ProcessWithTimeout:
    def __init__(self, timeout):
        self.timeout = timeout
        self.process = None

    def run(self, *args, **kwargs):
        def target():
            self.process = subprocess.Popen(*args, **kwargs)
            self.process.communicate()

        if self.timeout is not None:
            thread = threading.Thread(target=target)
            thread.start()

            thread.join(self.timeout)
            if thread.is_alive():
                self.process.terminate()
                thread.join(self.timeout)
                assert (not thread.is_alive())
                return (True, self.process.returncode)

            return (False, self.process.returncode)

        else:
            target()
            return (False, self.process.returncode)


class BinaryWrapper:
    def __init__(self, binary_path, dry_run):
        self._binary_path = os.path.abspath(
            maybe_add_exe_extension(binary_path))
        self._dry_run = dry_run

    def run(self, args, time_limit_sec=None, memory_limit_kb=None,
            suppress_output=True, cwd=None):
        if cwd is None:
            with TemporaryDirectory(dir=os.curdir) as tmp:
                return self._execute(args, tmp, time_limit_sec,
                                     memory_limit_kb, suppress_output)
        else:
            return self._execute(args, cwd, time_limit_sec,
                                 memory_limit_kb, suppress_output)

    def _execute(self, args, cwd, time_limit_sec=None, memory_limit_kb=None,
                 suppress_output=True):
        if not suppress_output:
            raise not NotImplementedError('pipe binary output')

        if self._dry_run:
            return Verdict.ACCEPTED
        if args is None:
            args = []

        exec_params = dict()

        exec_params['stdout'] = open(os.devnull, 'w')
        exec_params['stderr'] = open(os.devnull, 'w')

        if not _is_running_on_windows():
            def limit_process_resources():
                # The following code works on real Linux but crashes on WSL
                if time_limit_sec is not None:
                    # We hope that the code with 'kill by timer' logic works fine,
                    # but lets leave this rlimit still active until the new way of
                    # TLE detection will be properly tested.
                    import resource
                    resource.setrlimit(
                        resource.RLIMIT_CPU,
                        (time_limit_sec * 2, time_limit_sec * 2)
                    )
                if memory_limit_kb is not None:
                    # TODO: Remove this *temporary* hack
                    if not self._binary_path.endswith(('_asan', '_asan.exe')):
                        import resource
                        resource.setrlimit(
                            resource.RLIMIT_AS,
                            (memory_limit_kb * 1024, memory_limit_kb * 1024)
                        )

            exec_params['preexec_fn'] = limit_process_resources

        #try:
            # exitcode = call([self._binary_path] + args, cwd=cwd, **exec_params)

        proc = ProcessWithTimeout(timeout=time_limit_sec)
        (killed_by_timer, exitcode) = \
            proc.run([self._binary_path] + args, cwd=cwd, **exec_params)

        if killed_by_timer:
            return Verdict.TIME_LIMIT_EXCEEDED

        return Verdict.ACCEPTED if exitcode == 0 else Verdict.FAILED

        #except TimeoutExpired:
        #    return Verdict.TIME_LIMIT_EXCEEDED
        # TODO: Check MLE
