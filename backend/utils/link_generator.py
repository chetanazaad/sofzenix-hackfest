import secrets
import string


def generate_token(length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_unique_token(existing_tokens: set, length: int = 8, max_attempts: int = 100) -> str:
    for _ in range(max_attempts):
        token = generate_token(length)
        if token not in existing_tokens:
            return token
    raise RuntimeError("Could not generate unique token after max attempts.")


def generate_referral_code(length: int = 8) -> str:
    """Generate a short alphanumeric referral code for participants."""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))
