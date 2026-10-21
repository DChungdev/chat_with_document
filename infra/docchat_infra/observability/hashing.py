import hashlib
import hmac
from uuid import UUID


def hash_user_id(user_id: UUID | str, salt: str) -> str:
    """Băm một chiều có muối (HMAC-SHA256, 64 ký tự hex) — dùng cho log và telemetry."""
    return hmac.new(salt.encode(), str(user_id).encode(), hashlib.sha256).hexdigest()
