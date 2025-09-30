import random
import re
import string
import time
from openbb_ai.models import LlmMessage  # type: ignore[import-untyped]


def validate_api_key(token: str, api_key: str) -> bool:
    """Validate API key in header against pre-defined list of keys."""
    if not token:
        return False
    if token.replace("Bearer ", "").strip() == api_key:
        return True
    return False


async def sanitize_message(message: str) -> str:
    """Sanitize a message by escaping forbidden characters."""
    cleaned_message = re.sub(r"(?<!\{)\{(?!{)", "{{", message)
    cleaned_message = re.sub(r"(?<!\})\}(?!})", "}}", cleaned_message)
    return cleaned_message


async def is_last_message(message: LlmMessage, messages: list[LlmMessage]) -> bool:
    """Check if the message is the last human message in the conversation."""
    human_messages = [msg for msg in messages if msg.role == "human"]
    return message == human_messages[-1] if human_messages else False


async def generate_id(length: int = 2) -> str:
    """Generate a unique ID with a total length of 4 characters."""
    timestamp = int(time.time() * 1000) % 1000

    base36_chars = string.digits + string.ascii_lowercase

    def to_base36(num):
        result = ""
        while num > 0:
            result = base36_chars[num % 36] + result
            num //= 36
        return result.zfill(2)

    random_suffix = "".join(random.choices(base36_chars, k=length))
    return to_base36(timestamp) + random_suffix
