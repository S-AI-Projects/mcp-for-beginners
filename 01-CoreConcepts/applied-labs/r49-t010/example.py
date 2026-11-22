import sys


CLIENT_CAPABILITIES = {"tools", "resources"}
SERVER_CAPABILITIES = {"tools", "prompts"}


class CapabilityNotNegotiatedError(ValueError):
    pass


class CapabilityServer:
    def __init__(self, client_capabilities, server_capabilities):
        self.negotiated = client_capabilities & server_capabilities
        self.dispatch_count = 0

    def _dispatch(self, capability):
        self.dispatch_count += 1

        if capability == "tools":
            return "Mock tool result"

        raise ValueError(f"Unknown capability: {capability}")

    def invoke(self, capability):
        if capability not in self.negotiated:
            raise CapabilityNotNegotiatedError(
                f"Capability '{capability}' was not negotiated"
            )

        return self._dispatch(capability)


def main():
    capability = sys.argv[1] if len(sys.argv) > 1 else "tools"

    server = CapabilityServer(
        CLIENT_CAPABILITIES,
        SERVER_CAPABILITIES
    )

    print("Negotiated capabilities:", sorted(server.negotiated))

    try:
        result = server.invoke(capability)
        print("Result:", result)
        print("Dispatch calls:", server.dispatch_count)
        return 0

    except CapabilityNotNegotiatedError as error:
        print("Rejected before dispatch:", error)
        print("Dispatch calls:", server.dispatch_count)
        return 1


if __name__ == "__main__":
    sys.exit(main())
