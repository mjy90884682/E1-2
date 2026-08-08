import unittest

from scripts.capture_terminal_evidence import plain_transcript


class PlainTranscriptTest(unittest.TestCase):
    def test_keeps_prompts_and_echoed_input_while_normalizing_terminal_output(self) -> None:
        output = "\x1b[32m선택: \x1b[0m2\r\n문제: 예시\r\n"

        self.assertEqual(
            plain_transcript(output),
            "$ python -m quiz_game\n선택: 2\n문제: 예시\n",
        )


if __name__ == "__main__":
    unittest.main()
