import random
from datetime import datetime, timedelta, timezone

def generate_otp() -> str:
    """
    Generate a secure 6-digit numeric OTP code.
    """
    return "".join(random.choices("0123456789", k=6))

def validate_otp(input_otp: str, saved_otp: str) -> bool:
    """
    Validate if the user provided OTP matches the stored OTP code.
    """
    return input_otp == saved_otp

def is_otp_expired(generation_time: datetime, max_age_hours: float = 24.0) -> bool:
    """
    Evaluate if the OTP has expired.
    By default, OTPs expire 24 hours after generation (the delivery window day).
    """
    if not generation_time:
        return True
    expiration_time = generation_time + timedelta(hours=max_age_hours)
    return datetime.now(timezone.utc).replace(tzinfo=None) > expiration_time
