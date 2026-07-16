import hashlib

def generate_qr_hash(tracking_number: str) -> str:
    """
    Generate a secure SHA256 hash derived from the tracking number to act as the QR code payload.
    This hash is printed/rendered on the physical parcel label.
    """
    data = f"QR-{tracking_number}"
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def validate_qr_hash(scanned_hash: str, tracking_number: str) -> bool:
    """
    Validate if the scanned QR hash matches the generated hash for the given tracking number.
    Returns True if valid, False otherwise.
    """
    expected_hash = generate_qr_hash(tracking_number)
    return scanned_hash == expected_hash
