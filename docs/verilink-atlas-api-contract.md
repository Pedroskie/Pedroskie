# VeriLink Atlas API Contract v1.0

## Overview
The VeriLink Atlas API provides authenticated, read-focused access to the Integrity Engine so that public interfaces – including the Proof Console, Entity Pages, and the Redress Registry – can surface verifiable attestations. All endpoints serve JSON over HTTPS and are designed to be idempotent. Responses are signed by the Integrity Engine, allowing downstream services to preserve cryptographic assurances when relaying data to citizens.

## Versioning & Base URL
- **Base URL (production):** `https://api.verilink.atlas/v1`
- **Sandbox URL:** `https://sandbox.api.verilink.atlas/v1`
- **Semantic versioning:** Backwards-compatible changes increment the minor version; breaking changes increment the major version. Clients MUST specify the `Accept-Version` header when pinning to a specific release.

## Authentication & Authorization
- **Scheme:** OAuth 2.0 Client Credentials with mutual TLS.
- **Token endpoint:** `POST https://auth.verilink.atlas/oauth2/token`
- **Scopes:**
  - `integrity.read`: Required to access transaction proofs and institution indexes.
  - `redress.read`: Required to access redress registry records.
- **Headers:**
  - `Authorization: Bearer <access_token>`
  - `Accept: application/json`
  - `Content-Type: application/json` (for requests with bodies)
- Requests without valid credentials return `401 Unauthorized`.

## Common Response Envelope
```json
{
  "meta": {
    "request_id": "uuid",
    "timestamp": "2024-05-04T16:20:00Z",
    "signature": "base64-encoded-ed25519-signature"
  },
  "data": { /* resource-specific payload */ },
  "links": { /* optional HATEOAS links */ }
}
```
- `signature` is an Ed25519 signature computed over the canonicalized JSON body.
- Error responses use the same envelope with an `errors` array instead of `data`.

## Error Format
```json
{
  "meta": { ... },
  "errors": [
    {
      "code": "string",
      "title": "human-readable summary",
      "detail": "actionable description",
      "status": 404,
      "source": {
        "parameter": "transaction_id"
      }
    }
  ]
}
```
- Common error codes: `not_found`, `invalid_request`, `forbidden`, `rate_limited`, `internal_error`.

## Rate Limiting
- Default limit: 120 requests/minute per client.
- Headers returned:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`

---

## Resources

### 1. Transaction Proofs (Proof Console)
Supports retrieval of a single transaction's integrity status, attestation metadata, and Merkle inclusion proof.

#### Endpoint: Get Transaction Proof
- **Method:** `GET`
- **Path:** `/transactions/{transaction_id}`
- **Scopes:** `integrity.read`
- **Path Parameters:**
  - `transaction_id` (string, required): UUID or hash assigned by the Integrity Engine.
- **Query Parameters:**
  - `include_merkle` (boolean, default `true`): Toggle inclusion of Merkle proof blob.
  - `ledger_height` (integer, optional): If provided, verifies inclusion relative to a historical ledger snapshot.
- **Response `data` Object:**
```json
{
  "transaction_id": "uuid",
  "status": "verified | pending | revoked",
  "attestation_hash": "hex",
  "attested_at": "2024-04-22T11:43:27Z",
  "integrity_score": 0.998,
  "merkle_proof": {
    "root_hash": "hex",
    "leaf_hash": "hex",
    "siblings": ["hex", "hex"],
    "depth": 18,
    "algorithm": "sha-256"
  },
  "redress": {
    "superseded_by": "attestation_id | null",
    "registry_link": "https://atlas.verilink.redress/records/{attestation_id}"
  },
  "links": {
    "self": "/transactions/{transaction_id}",
    "entity": "/institutions/{institution_id}"
  }
}
```
- If `include_merkle=false`, the `merkle_proof` object is omitted.

#### Endpoint: Validate Merkle Proof
- **Method:** `POST`
- **Path:** `/transactions/validate`
- **Scopes:** `integrity.read`
- **Description:** Deterministically verifies a provided Merkle proof against the Integrity Engine's canonical ledger state.
- **Request Body:**
```json
{
  "transaction_id": "uuid",
  "root_hash": "hex",
  "leaf_hash": "hex",
  "siblings": ["hex"],
  "algorithm": "sha-256"
}
```
- **Response `data`:**
```json
{
  "transaction_id": "uuid",
  "is_valid": true,
  "ledger_height": 124553,
  "verified_at": "2024-05-01T09:14:51Z"
}
```

---

### 2. Institutions (Entity Pages)
Provides Integrity Transparency Index (ITI) scores and summary data for each institution.

#### Endpoint: List Institutions
- **Method:** `GET`
- **Path:** `/institutions`
- **Scopes:** `integrity.read`
- **Query Parameters:**
  - `page` (integer, default `1`)
  - `page_size` (integer, default `25`, max `100`)
  - `jurisdiction` (string, optional)
  - `category` (string, optional; e.g., `public_agency`, `financial`, `ngo`)
  - `search` (string, optional; case-insensitive match on name or identifier)
- **Response `data` Array Items:**
```json
{
  "institution_id": "uuid",
  "name": "UnityFund Foundation",
  "iti_score": 87.4,
  "last_audited_at": "2024-03-30T00:00:00Z",
  "jurisdiction": "US-CA",
  "category": "ngo",
  "links": {
    "self": "/institutions/{institution_id}",
    "transparency_report": "/institutions/{institution_id}/reports/latest"
  }
}
```
- Pagination metadata is provided via `meta.pagination` with `page`, `page_size`, `total_pages`, and `total_items`.

#### Endpoint: Get Institution Detail
- **Method:** `GET`
- **Path:** `/institutions/{institution_id}`
- **Scopes:** `integrity.read`
- **Path Parameters:**
  - `institution_id` (string, required)
- **Response `data`:**
```json
{
  "institution_id": "uuid",
  "name": "UnityFund Foundation",
  "integrity_transparency_index": {
    "completeness": 0.96,
    "timeliness": 0.91,
    "truthfulness": 0.99,
    "weighted_score": 92.1,
    "methodology_version": "2024-Q1"
  },
  "governance_summary": {
    "attestations_total": 542,
    "attestations_verified": 538,
    "open_investigations": 1,
    "last_integrity_event": "2024-04-25T08:12:09Z"
  },
  "contacts": {
    "integrity_officer": "mailto:integrity@unityfund.org",
    "public_disclosure": "https://unityfund.org/transparency"
  },
  "links": {
    "proof_console": "/transactions?institution_id={institution_id}",
    "redress_registry": "/redress?institution_id={institution_id}"
  }
}
```

#### Endpoint: Get Latest Transparency Report
- **Method:** `GET`
- **Path:** `/institutions/{institution_id}/reports/latest`
- **Scopes:** `integrity.read`
- **Response `data`:**
```json
{
  "institution_id": "uuid",
  "report_id": "uuid",
  "period_start": "2024-01-01",
  "period_end": "2024-03-31",
  "summary": "text/markdown",
  "iti_delta": -1.7,
  "supporting_documents": [
    {
      "type": "pdf",
      "title": "Quarterly Integrity Audit",
      "url": "https://cdn.verilink.atlas/reports/{report_id}.pdf",
      "hash": "sha256:..."
    }
  ]
}
```

---

### 3. Redress Registry
Publishes superseding attestation records for revoked or amended proofs, enabling affected parties to trace remediation steps.

#### Endpoint: List Redress Records
- **Method:** `GET`
- **Path:** `/redress`
- **Scopes:** `redress.read`
- **Query Parameters:**
  - `institution_id` (string, optional)
  - `transaction_id` (string, optional)
  - `status` (enum: `open`, `resolved`, `dismissed`)
  - `since` (ISO-8601 timestamp, optional): Return records updated after this moment.
- **Response `data` Array Items:**
```json
{
  "redress_id": "uuid",
  "institution_id": "uuid",
  "transaction_id": "uuid",
  "superseding_attestation_id": "uuid",
  "reason": "data_correction",
  "status": "open",
  "filed_at": "2024-04-12T15:00:00Z",
  "updated_at": "2024-04-22T09:11:05Z",
  "next_review_at": "2024-05-06T00:00:00Z",
  "links": {
    "self": "/redress/{redress_id}",
    "superseding_attestation": "/attestations/{superseding_attestation_id}"
  }
}
```

#### Endpoint: Get Redress Record Detail
- **Method:** `GET`
- **Path:** `/redress/{redress_id}`
- **Scopes:** `redress.read`
- **Response `data`:**
```json
{
  "redress_id": "uuid",
  "transaction_id": "uuid",
  "superseding_attestation": {
    "attestation_id": "uuid",
    "issued_at": "2024-04-20T10:32:44Z",
    "issuer": {
      "type": "institution",
      "id": "uuid",
      "name": "UnityFund Foundation"
    },
    "summary": "Corrected allocation data for Q1 disbursement.",
    "document_url": "https://cdn.verilink.atlas/attestations/{attestation_id}.json",
    "document_hash": "sha256:..."
  },
  "redress_panel": {
    "members": [
      {
        "name": "Dr. Amina Patel",
        "role": "Independent Auditor",
        "affiliation": "Civic Trust Network"
      }
    ],
    "vote": "2-1",
    "decision_at": "2024-04-21T18:45:00Z"
  },
  "status": "resolved",
  "resolution_summary": "Allocation corrected, restitution paid to impacted grantees.",
  "public_notice_url": "https://atlas.verilink.redress/notices/{redress_id}"
}
```

---

## Attestation Reference Endpoint
Redress records link to superseding attestations resolved by the Integrity Engine.

#### Endpoint: Get Attestation
- **Method:** `GET`
- **Path:** `/attestations/{attestation_id}`
- **Scopes:** `integrity.read`
- **Response `data`:**
```json
{
  "attestation_id": "uuid",
  "version": 3,
  "issued_at": "2024-04-20T10:32:44Z",
  "valid_from": "2024-04-20T00:00:00Z",
  "valid_until": null,
  "subject": {
    "transaction_id": "uuid",
    "institution_id": "uuid"
  },
  "payload_hash": "sha256:...",
  "merkle_root": "hex",
  "previous_attestation_id": "uuid",
  "supersedes": ["transaction_attestation_v2"],
  "uri": "ipfs://bafy...",
  "signature": "base64"
}
```

---

## Webhooks (Optional Extension)
- Clients MAY register HTTPS endpoints to receive real-time notifications when transaction statuses change or when new redress records are issued.
- **Registration Endpoint:** `POST /webhooks`
- **Event Types:** `transaction.status_changed`, `redress.created`, `redress.updated`.
- Events are delivered with JSON payloads signed using the same Ed25519 scheme as synchronous responses.

## Change Management
- Schema changes are announced at least 30 days before deployment via the Integrity Bulletin.
- Deprecated fields remain available for 90 days with the `deprecated` flag in the `meta` envelope.

## Compliance & Auditability
- All access is logged with request metadata and OAuth client identifiers.
- The ledger maintains proofs for 10 years; archival queries can be requested via `/support/tickets` (outside scope of this API).
- The API conforms to the UnityFund treasury policy: hot wallet exposure never exceeds 20% of reserve balances, multisig thresholds are enforced on mutation endpoints (reserved for future write APIs), and Base L2 transactions are only confirmed after 6 blocks before proofs are marked `verified`.
