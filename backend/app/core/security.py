import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple
import bcrypt
import jwt

from app.core.config import settings

VALID_ROLES = {"ADMIN", "ANALYST", "VIEWER"}


def hash_password(password: str) -> str:
    """Securely hash a plaintext password using bcrypt with 12 salt rounds."""
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash in constant time."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def create_access_token(
    subject: str,
    user_id: int,
    role: str,
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate a signed HS256 JWT access token with normalized expiration."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)

    to_encode = {
        "sub": subject,
        "user_id": user_id,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if extra_claims:
        to_encode.update(extra_claims)

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and cryptographically verify a JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["exp", "sub", "user_id", "role"]},
        )
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


class LoginRateLimiter:
    """
    In-memory rate limiter tracking failed login attempts per key (IP / username)
    to defend against brute-force attacks without requiring external Redis in local dev.
    """
    def __init__(self, max_attempts: int = 5, lock_duration_seconds: int = 900):
        self.max_attempts = max_attempts
        self.lock_duration_seconds = lock_duration_seconds
        # key -> (failed_count, first_failure_timestamp, locked_until_timestamp)
        self._state: Dict[str, Tuple[int, float, float]] = {}

    def is_locked(self, key: str) -> Tuple[bool, int]:
        """Check if key is locked. Returns (is_locked, remaining_seconds)."""
        now = time.time()
        record = self._state.get(key)
        if not record:
            return False, 0

        failed_count, _, locked_until = record
        if locked_until > now:
            return True, int(locked_until - now)
        elif locked_until > 0 and locked_until <= now:
            # Lock expired
            del self._state[key]
            return False, 0
        return False, 0

    def record_failure(self, key: str) -> Tuple[bool, int]:
        """
        Record a failed attempt. If threshold exceeded, lock key.
        Returns (is_locked_now, remaining_seconds).
        """
        now = time.time()
        record = self._state.get(key)

        if not record:
            self._state[key] = (1, now, 0.0)
            return False, 0

        failed_count, first_ts, locked_until = record
        # Reset window if first attempt was longer than lock_duration ago
        if now - first_ts > self.lock_duration_seconds and locked_until <= now:
            self._state[key] = (1, now, 0.0)
            return False, 0

        new_count = failed_count + 1
        if new_count >= self.max_attempts:
            new_locked_until = now + self.lock_duration_seconds
            self._state[key] = (new_count, first_ts, new_locked_until)
            return True, self.lock_duration_seconds
        else:
            self._state[key] = (new_count, first_ts, 0.0)
            return False, 0

    def record_success(self, key: str) -> None:
        """Clear failures on successful authentication."""
        self._state.pop(key, None)

    def reset(self) -> None:
        """Clear all rate limit state (useful in tests)."""
        self._state.clear()


# Global rate limiter instance
login_rate_limiter = LoginRateLimiter(
    max_attempts=settings.MAX_FAILED_LOGIN_ATTEMPTS,
    lock_duration_seconds=settings.ACCOUNT_LOCK_MINUTES * 60,
)
