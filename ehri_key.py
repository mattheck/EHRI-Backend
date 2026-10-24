"""Load the EHRI signing key from deployment-managed storage."""

import os


def load_private_key():
    """Read the signing key from EHRI_PRIVATE_KEY_PATH without a repository fallback."""
    key_path = os.environ.get("EHRI_PRIVATE_KEY_PATH")
    if not key_path:
        raise RuntimeError("EHRI_PRIVATE_KEY_PATH must point to a signing key outside the repository")
    with open(key_path, "r", encoding="utf-8") as key_file:
        return key_file.read()
