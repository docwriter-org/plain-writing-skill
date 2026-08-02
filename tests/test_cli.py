import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from plain_writing.cli import main


class CliTests(unittest.TestCase):
    def run_cli(self, args: list[str], stdin: str) -> tuple[int, str]:
        output = io.StringIO()
        with patch("sys.stdin", io.StringIO(stdin)), redirect_stdout(output):
            status = main(args)
        return status, output.getvalue()

    def test_reads_plain_text_from_stdin(self) -> None:
        status, output = self.run_cli([], "The build passed all tests.")
        self.assertEqual(status, 0)
        self.assertEqual(output.strip(), "0 violations")

    def test_returns_nonzero_for_a_violation(self) -> None:
        status, output = self.run_cli([], "This is really robust.")
        self.assertEqual(status, 1)
        self.assertIn("PW005", output)
        self.assertIn("PW009", output)

    def test_json_report_is_machine_readable(self) -> None:
        status, output = self.run_cli(
            ["--format", "json"], "The build passed all tests."
        )
        self.assertEqual(status, 0)
        self.assertTrue(json.loads(output)["ok"])

    def test_hook_allows_plain_response(self) -> None:
        event = {
            "stop_hook_active": False,
            "last_assistant_message": "The build passed all tests.",
        }
        status, output = self.run_cli(["--hook"], json.dumps(event))
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(output), {})

    def test_hook_blocks_and_requests_rewrite(self) -> None:
        event = {
            "stop_hook_active": False,
            "last_assistant_message": "This is not just robust — it really matters.",
        }
        status, output = self.run_cli(["--hook"], json.dumps(event))
        decision = json.loads(output)
        self.assertEqual(status, 0)
        self.assertEqual(decision["decision"], "block")
        self.assertIn("PW001", decision["reason"])
        self.assertIn("PW005", decision["reason"])
        self.assertIn("PW007", decision["reason"])

    def test_hook_does_not_create_a_correction_loop(self) -> None:
        event = {
            "stop_hook_active": True,
            "last_assistant_message": "This is really robust.",
        }
        status, output = self.run_cli(["--hook"], json.dumps(event))
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(output), {})


if __name__ == "__main__":
    unittest.main()
