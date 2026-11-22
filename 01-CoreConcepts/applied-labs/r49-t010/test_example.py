
import unittest

from example import (
    CLIENT_CAPABILITIES,
    SERVER_CAPABILITIES,
    CapabilityServer,
    CapabilityNotNegotiatedError,
)


class TestCapabilityNegotiation(unittest.TestCase):

    def test_negotiated_capabilities(self):
        server = CapabilityServer(CLIENT_CAPABILITIES, SERVER_CAPABILITIES)
        self.assertEqual(server.negotiated, {"tools"})

    def test_tool_invocation(self):
        server = CapabilityServer(CLIENT_CAPABILITIES, SERVER_CAPABILITIES)
        result = server.invoke("tools")
        self.assertEqual(result, "Mock tool result")
        self.assertEqual(server.dispatch_count, 1)

    def test_resources_rejected(self):
        server = CapabilityServer(CLIENT_CAPABILITIES, SERVER_CAPABILITIES)
        with self.assertRaises(CapabilityNotNegotiatedError):
            server.invoke("resources")
        self.assertEqual(server.dispatch_count, 0)

    def test_rejection_happens_before_dispatch(self):
        server = CapabilityServer(CLIENT_CAPABILITIES, SERVER_CAPABILITIES)
        with self.assertRaises(CapabilityNotNegotiatedError):
            server.invoke("resources")
        self.assertNotIn("resources", server.negotiated)
        self.assertEqual(server.dispatch_count, 0)

    def test_prompts_not_negotiated(self):
        server = CapabilityServer(CLIENT_CAPABILITIES, SERVER_CAPABILITIES)
        self.assertNotIn("prompts", server.negotiated)

    def test_rejected_call_does_not_increment_dispatch(self):
        server = CapabilityServer(CLIENT_CAPABILITIES, SERVER_CAPABILITIES)
        with self.assertRaises(CapabilityNotNegotiatedError):
            server.invoke("resources")
        self.assertEqual(server.dispatch_count, 0)


if __name__ == "__main__":
    unittest.main()
