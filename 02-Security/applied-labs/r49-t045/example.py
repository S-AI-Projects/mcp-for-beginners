import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def local_verifier(token):
    """Mock verifier using local fixture tokens."""
    identities = {
        "demo-valid-token": "student-001"
    }
    return identities.get(token)


def authenticate(token, verifier=local_verifier):
    if not token:
        logger.info("Authentication result: unauthenticated")
        return {"status": "unauthenticated", "subject": None}

    subject = verifier(token)

    if subject is None:
        logger.info("Authentication result: invalid")
        return {"status": "invalid", "subject": None}

    logger.info("Authentication result: authenticated")
    return {"status": "authenticated", "subject": subject}


if __name__ == "__main__":
    for token in [None, "wrong-token", "demo-valid-token"]:
        print(authenticate(token))