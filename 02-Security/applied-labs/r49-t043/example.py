"""Local demonstration of a bearer-token authentication boundary."""

def authenticate(token, verifier):
    trace = []
    safe_logs = []

    # Step 1: Check whether a token was supplied.
    token_present = token is not None and token != ""
    trace.append({
        "step": "token_received",
        "token_present": token_present
    })

    if not token_present:
        identity = None
        status = "unauthenticated"
        verification = "missing"
    else:
        # Step 2: Verify the token without logging its value.
        identity = verifier(token)

        if identity is None:
            status = "invalid"
            verification = "rejected"
        else:
            status = identity
            verification = "valid"

    trace.append({
        "step": "verification",
        "result": verification
    })

    trace.append({
        "step": "identity",
        "subject": identity
    })

    trace.append({
        "step": "final",
        "output": status
    })

    safe_logs.append("Authentication processed; token value redacted.")

    # Invariant: final output must match the verification state.
    if verification == "missing":
        assert status == "unauthenticated"
    elif verification == "rejected":
        assert status == "invalid"
    else:
        assert status == identity and identity is not None

    return {
        "status": status,
        "trace": trace,
        "logs": safe_logs
    }


def fixture_verifier(token):
    """A small local fixture; never logs the supplied token."""
    identities = {
        "fixture-token-123": "student-01"
    }
    return identities.get(token)


if __name__ == "__main__":
    import json

    scenarios = [
        ("missing", None),
        ("unknown", "wrong-token"),
        ("known", "fixture-token-123")
    ]

    for name, token in scenarios:
        result = authenticate(token, fixture_verifier)
        print(name + ":")
        print(json.dumps(result, indent=2))
