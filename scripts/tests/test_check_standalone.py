# SPDX-License-Identifier: Apache-2.0
"""Failure-path controls for the CI driver, without invoking the test suites."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    'ci_driver', Path(__file__).resolve().parents[1]/'check_standalone.py')
DRIVER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DRIVER)


class DriverFailures(unittest.TestCase):
    def invoke(self, output, subprocess_effect):
        with patch.object(sys, 'argv', ['check_standalone.py', '--output', str(output)]), \
             patch.object(DRIVER.importlib.metadata, 'version', return_value='test-only'), \
             patch.object(DRIVER.subprocess, 'run', side_effect=subprocess_effect), \
             contextlib.redirect_stdout(io.StringIO()):
            return DRIVER.main()

    def test_zero_discovered_tests_is_failure(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td)/'output'
            response = subprocess.CompletedProcess([], 0, b'', b'Ran 0 tests in 0.000s\n\nOK\n')
            self.assertEqual(self.invoke(output, [response]), 1)
            result = json.loads((output/'summary.json').read_text())
            self.assertEqual(result['status'], 'FAIL')
            self.assertIn('minimum expected test count', result['error'])

    def test_timeout_retains_partial_logs_and_failed_command(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td)/'output'
            error = subprocess.TimeoutExpired(['synthetic'], 120,
                                               output=b'partial-out', stderr=b'partial-err')
            self.assertEqual(self.invoke(output, [error]), 1)
            result = json.loads((output/'summary.json').read_text())
            self.assertEqual(result['status'], 'FAIL')
            commands = json.loads((output/'commands.json').read_text())
            self.assertEqual(len(commands), 1)
            self.assertTrue(commands[0]['timed_out'])
            self.assertIsNone(commands[0]['exit_code'])
            self.assertEqual((output/'standalone-tests.stdout').read_bytes(), b'partial-out')
            self.assertEqual((output/'standalone-tests.stderr').read_bytes(), b'partial-err')


if __name__ == '__main__':
    unittest.main()
