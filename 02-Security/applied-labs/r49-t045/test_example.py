import unittest
from example import authenticate


class AuthenticationTests(unittest.TestCase):

    def test_missing_token(self):
        self.assertEqual(
            authenticate(None),
            {"status": "unauthenticated", "subject": None}
        )

    def test_unknown_token(self):
        self.assertEqual(
            authenticate("wrong-token"),
            {"status": "invalid", "subject": None}
        )

    def test_valid_token(self):
        self.assertEqual(
            authenticate("demo-valid-token"),
            {"status": "authenticated", "subject": "student-001"}
        )

    def test_custom_verifier(self):
        def verifier(token):
            return "user-123" if token == "custom-token" else None

        self.assertEqual(
            authenticate("custom-token", verifier),
            {"status": "authenticated", "subject": "user-123"}
        )

    def test_token_is_not_logged(self):
        with self.assertLogs("example", level="INFO") as captured:
            authenticate("secret-test-token")

        self.assertNotIn("secret-test-token", "\n".join(captured.output))


if __name__ == "__main__":
    unittest.main()