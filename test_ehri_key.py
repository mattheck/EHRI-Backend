"""Tests for external signing-key configuration."""

import os
import unittest
from unittest.mock import mock_open, patch

from ehri_key import load_private_key


class ExternalKeyTests(unittest.TestCase):
    """Check configuration failures and externally provided key loading."""

    def test_missing_configuration_does_not_read_a_local_key(self):
        with patch.dict(os.environ, {}, clear=True), patch("builtins.open") as read:
            with self.assertRaisesRegex(RuntimeError, "EHRI_PRIVATE_KEY_PATH"):
                load_private_key()
            read.assert_not_called()

    def test_configured_path_is_read(self):
        with patch.dict(os.environ, {"EHRI_PRIVATE_KEY_PATH": "/deployment/signing.pem"}):
            with patch("builtins.open", mock_open(read_data="test-key-placeholder")) as read:
                self.assertEqual("test-key-placeholder", load_private_key())
                read.assert_called_once_with("/deployment/signing.pem", "r", encoding="utf-8")

    def test_missing_configured_file_fails_without_fallback(self):
        with patch.dict(os.environ, {"EHRI_PRIVATE_KEY_PATH": "/missing/signing.pem"}):
            with patch("builtins.open", side_effect=FileNotFoundError):
                with self.assertRaises(FileNotFoundError):
                    load_private_key()


if __name__ == "__main__":
    unittest.main()
