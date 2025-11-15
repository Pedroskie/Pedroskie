⸻

🔐 VeriLink PGP Key Management & Compliance Policy

Document ID: verilink_pgp_policy.md
Version: v1.0.0
Created: 2025-10-15
Maintainer: Pedro L. Rentas Torres — Security Lead

⸻

1. Purpose

This document defines the policy and operational procedures for generating, maintaining, rotating, and auditing PGP keys used for Bugcrowd triage, security disclosures, and client encryption channels across VeriLink / FlowLedger environments.

⸻

2. Scope

Applies to:
• All VeriLink triage and disclosure communication channels
• Any PGP keypair used for receiving encrypted vulnerability reports
• All employees or AI-assisted agents authorized to decrypt Bugcrowd or customer submissions

⸻

3. Key Lifecycle Policy

| Phase       | Description                                                                 | Responsible   | Frequency                      |
|-------------|------------------------------------------------------------------------------|---------------|---------------------------------|
| Generation  | Create new 4096-bit RSA + RSA keypair via `gpg --full-generate-key`          | Security Lead | Initial + annual               |
| Export      | Public key exported as ASCII (`verilink_triage_pub.asc`) and uploaded to Bugcrowd | Security Lead | On creation                    |
| Backup      | Secret key (`verilink_triage_secret.asc`) stored on encrypted offline media  | Security Lead | Immediately after generation   |
| Verification| Test encryption/decryption cycle                                             | Security Team | Each rotation                  |
| Rotation    | Generate new keypair every 12 months or upon compromise notification         | Security Lead | Annual (October cycle)         |
| Revocation  | Issue revoke certificate via `gpg --gen-revoke` and publish on Bugcrowd & keyservers | Security Lead | As needed                      |

⸻

4. Operational Commands Reference

# Generate new keypair
gpg --full-generate-key

# List & verify fingerprint
gpg --list-keys
gpg --fingerprint triage@verilink.example

# Export public key (for Bugcrowd)
gpg --armor --export triage@verilink.example > verilink_triage_pub.asc

# Verify export integrity
gpg --import --dry-run --import-options show-only verilink_triage_pub.asc

# Securely backup private key
gpg --export-secret-keys --armor triage@verilink.example > verilink_triage_secret.asc

# Test encryption/decryption
echo "verification test" | gpg --encrypt --armor --recipient triage@verilink.example > testmsg.asc
gpg --decrypt testmsg.asc

⸻

5. Compliance and Audit Checklist

| Item                                | Status       | Verified By            | Date       |
|-------------------------------------|--------------|------------------------|------------|
| Key generated (4096 bit)            | ✅            | Pedro L. Rentas Torres | 2025-10-15 |
| Public key uploaded to Bugcrowd     | ✅            | Pedro L. Rentas Torres | 2025-10-15 |
| Fingerprint published in program brief | ✅        | Security Ops           | 2025-10-15 |
| Secret key securely backed up       | ✅            | Security Ops           | 2025-10-15 |
| Encryption round-trip verified      | ✅            | QA Engineer            | 2025-10-15 |
| Next rotation scheduled             | 🔄 2026-10-01 | Pedro L. Rentas Torres | —          |

⸻

6. Retention & Storage
• Public key: stored in repository (/security/keys/) and Bugcrowd portal.
• Secret key: encrypted offline vault only (never committed to Git or cloud storage).
• Rotation records and audit logs: retained for 5 years minimum to satisfy Bugcrowd and client audit requirements.

⸻

7. Integrity Anchoring (Optional)

Every finalized verilink_pgp_policy.md revision is anchored to FlowLedger as a policy.pgp event:

{
  "type": "policy.pgp",
  "version": "v1.0.0",
  "author": "Pedro L. Rentas Torres",
  "sha256": "<computed_digest>",
  "ots": "proofs/policy.pgp.ots",
  "ts": 1739568300
}

This ensures tamper-proof auditability across FlowLedger and OTS chains.

⸻

8. Next Review Cycle

Scheduled Review: October 2026
Reviewer: Security Ops Lead or Designated Auditor
Action: Confirm new key generation, revoke old key, update fingerprint in Bugcrowd brief, anchor new policy revision to FlowLedger.

⸻
