import unittest

from plain_writing.checker import check_text


class CheckerTests(unittest.TestCase):
    def rules(self, text: str) -> set[str]:
        return {item.rule for item in check_text(text)}

    def test_accepts_plain_prose(self) -> None:
        text = (
            "The build passed because all 42 tests completed successfully. "
            "You can merge the change after the required review."
        )
        self.assertEqual(check_text(text), [])

    def test_finds_disallowed_punctuation(self) -> None:
        rules = self.rules('The “fast” path takes 10–20 ms — usually · not always.')
        self.assertTrue({"PW001", "PW002", "PW003", "PW004"} <= rules)

    def test_ignores_code_and_urls(self) -> None:
        text = (
            "Run `printf 'quietly — done'`.\n"
            "```text\nThis — code stays exact.\n```\n"
            "See https://example.com/a—b."
        )
        self.assertEqual(check_text(text), [])

    def test_finds_empty_language_and_filler(self) -> None:
        rules = self.rules(
            "It is worth noting that this robust tool really leverages the cache."
        )
        self.assertTrue({"PW005", "PW006"} <= rules)
        banned = [
            item
            for item in check_text("The robust tool is really useful.")
            if item.rule == "PW005"
        ]
        self.assertEqual(len(banned), 1)

    def test_finds_negative_parallel_and_vague_source(self) -> None:
        rules = self.rules(
            "Experts say it is not just a parser but a complete platform."
        )
        self.assertTrue({"PW007", "PW008"} <= rules)

    def test_finds_vague_sentence_openers(self) -> None:
        rules = self.rules(
            "This fixes the issue. The result is faster. Three things changed."
        )
        self.assertTrue({"PW009", "PW010", "PW011"} <= rules)

    def test_finds_analogy_pivot_colon_and_empty_opener(self) -> None:
        rules = self.rules(
            "The cache is like a shelf. But it has one limit. "
            "Clearly, the conclusion is simple: the cache wins."
        )
        self.assertTrue({"PW012", "PW013", "PW014", "PW015"} <= rules)

    def test_finds_title_case_heading_and_bold_heading(self) -> None:
        rules = self.rules(
            "# How To Install This Tool\n\n"
            "**Important Information**\n\n"
            "Follow the steps below."
        )
        self.assertTrue({"PW016", "PW017"} <= rules)

    def test_finds_stacked_questions_and_short_sentences(self) -> None:
        rules = self.rules(
            "Does it work? Does it scale? Can we ship it?"
        )
        self.assertTrue({"PW018", "PW019"} <= rules)

    def test_finds_three_clause_sentence(self) -> None:
        rules = self.rules(
            "The parser reads the file, and the validator checks it, "
            "and the writer saves it."
        )
        self.assertIn("PW020", rules)

    def test_finds_formatted_and_inline_lists(self) -> None:
        text = (
            "The checker finds filler, vague claims, and decorative punctuation.\n\n"
            "- Remove filler.\n"
            "- Name each source."
        )
        rules = self.rules(text)
        self.assertTrue({"PW021", "PW022"} <= rules)

    def test_allows_two_related_items(self) -> None:
        self.assertNotIn(
            "PW022",
            self.rules("The checker reports the line and matching text."),
        )

    def test_requires_approved_example_introducer(self) -> None:
        rules = self.rules("Some files, such as settings.json, need exact names.")
        self.assertIn("PW023", rules)
        self.assertNotIn(
            "PW023",
            self.rules("For example, settings.json needs its exact name."),
        )
        self.assertNotIn(
            "PW023",
            self.rules("E.g., settings.json needs its exact name."),
        )

    def test_finds_vague_backward_reference(self) -> None:
        self.assertIn(
            "PW024",
            self.rules("Both patterns make the prose feel staged."),
        )

    def test_reports_source_location(self) -> None:
        violation = check_text("A plain first line.\nThis is vague.")[0]
        self.assertEqual((violation.line, violation.column), (2, 1))
        self.assertEqual(violation.excerpt, "This is vague.")


if __name__ == "__main__":
    unittest.main()
