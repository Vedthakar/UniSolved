from __future__ import annotations

import unittest

from streamlit.testing.v1 import AppTest


class StreamlitAppTests(unittest.TestCase):
    def test_landing_page_is_default_view(self) -> None:
        app = AppTest.from_file("UniSolved_WEBSITE.py")

        app.run()

        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.error), 0)
        self.assertTrue(
            any("UniSolved helps students go from" in markdown.value for markdown in app.markdown)
        )

    def test_starter_prompt_does_not_nest_chat_messages(self) -> None:
        app = AppTest.from_file("UniSolved_WEBSITE.py")

        app.run()
        _find_button(app, "Launch Chat Demo").click().run()
        _find_button(app, "I'm struggling in CSC108 and want someone who speaks Hindi.").click().run()

        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.error), 0)
        self.assertGreaterEqual(len(app.markdown), 1)


def _find_button(app: AppTest, label: str):
    for button in app.button:
        if button.label == label:
            return button
    raise AssertionError(f"Button with label {label!r} was not found.")


if __name__ == "__main__":
    unittest.main()
