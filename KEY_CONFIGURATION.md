# Signing key configuration

Set `EHRI_PRIVATE_KEY_PATH` to a signing key supplied by deployment-managed storage outside the repository before making authenticated API requests. Missing configuration or an unreadable file fails without falling back to a repository key. Keep the key readable only by the application account.

Run the focused tests with `python3 -m unittest test_ehri_key`.

The previously tracked signing key must be treated as compromised until its issuer confirms revocation or replacement. This change removes the file from the proposed current tree only. It does not revoke the key or remove it from Git history, existing clones, cached views, or backups. Those actions require a separately approved remediation plan and verification.
