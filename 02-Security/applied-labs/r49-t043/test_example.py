import unittest

from example import authenticate, fixture_verifier


class AuthenticationTests(unittest.TestCase):

    def test_missing_token(self):
        result = authenticate(None, fixture_verifier)
        self.assertEqual(result["status"], "unauthenticated")
        self.assertEqual(result["trace"][1]["result"], "missing")

    def test_empty_token(self):
        result = authenticate("", fixture_verifier)
        self.assertEqual(result["status"], "unauthenticated")

    def test_unknown_token(self):
        result = authenticate("wrong-token", fixture_verifier)
        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["trace"][1]["result"], "rejected")

    def test_known_token(self):
        result = authenticate("fixture-token-123", fixture_verifier)
        self.assertEqual(result["status"], "student-01")
        self.assertEqual(result["trace"][1]["result"], "valid")
        self.assertEqual(result["trace"][2]["subject"], "student-01")

    def test_token_is_not_logged(self):
        secret = "my-secret-token"
        result = authenticate(secret, fixture_verifier)
        self.assertNotIn(secret, str(result["logs"]))

    def test_verifier_failure(self):
        def broken_verifier(token):
            raise RuntimeError("Verifier unavailable")

        with self.assertRaises(RuntimeError):
            authenticate("some-token", broken_verifier)


if __name__ == "__main__":
    unittest.main()
