- 👋 Hi, I’m @Pedroskie
- 👀 I’m interested in ...
- 🌱 I’m currently learning ...
- 💞️ I’m looking to collaborate on ...
- 📫 How to reach me ...

## 🛡️ Verifiable Releases & Integrity CLI

Every official UnityFund Integrity Engine release is automatically anchored to the Bitcoin blockchain using **OpenTimestamps** (OTS) to provide an immutable, public proof of existence for the exact code bundle.

### How We Release (The Single Command)

To ensure this continuous chain of trust, all releases are created using a single, automated script: `unityfund_integrity.sh`.

Any UnityFund developer can produce a fully proof-verified release by running:

```bash
./unityfund_integrity.sh <version>
```

This single command handles bundling, hashing, OTS stamping, committing the proof, running the OTS verification, and publishing the final GitHub release.

### How to Verify Our Releases

Auditors and users can independently verify the provenance of any release (vX.Y.Z) by following the steps below:

* Download the official release bundle (`UnityFund_Integrity_Engine_vX.Y.Z.zip`) from our GitHub releases page.
* Compute its SHA-256 hash locally.
* Compare the computed hash with the stamp contained in the committed OTS proof file, located in our repository at `integrity/vX.Y.Z_release_anchor.ots`.

If the OTS verification is successful, the release is 💚 STILL VERIFIED and guaranteed to be the code released at that specific, provable time.

### VeriLink Integrity Release v1.0.1

The final step to produce the VeriLink Integrity Release v1.0.1 bundle is to archive the verified artifacts into a single immutable package:

```bash
zip -r verilink-integrity-v1.0.1-release.zip verilink-integrity-v1.0.1-release/
```

**What this does**

- `zip -r` creates a compressed archive recursively so every file and directory is captured.
- `verilink-integrity-v1.0.1-release.zip` is the resulting release artifact.
- `verilink-integrity-v1.0.1-release/` points to the directory that contains the verification bundle, micro-anchor data, and documentation.

**Expected output**

```
  adding: verilink-integrity-v1.0.1-release/ (stored 0%)
  adding: verilink-integrity-v1.0.1-release/verilink-integrity-verification-v1.0.1.zip (deflated 64%)
  adding: verilink-integrity-v1.0.1-release/verilink-integrity-anchor-v1.0.1-sums.zip (deflated 58%)
  adding: verilink-integrity-v1.0.1-release/flowledger_anchor_v8.jsonl (deflated 42%)
  adding: verilink-integrity-v1.0.1-release/README_RELEASE.md (deflated 35%)
```

This creates `verilink-integrity-v1.0.1-release.zip`, capturing the complete chain from source, to artifact, to micro-anchor, to ledger, and finally to Bitcoin consensus—delivering an independently verifiable, cryptographically reproducible release bundle.

<!---
Pedroskie/Pedroskie is a ✨ special ✨ repository because its `README.md` (this file) appears on your GitHub profile.
You can click the Preview link to take a look at your changes.
--->
