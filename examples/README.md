# PENIN-Ω Examples

This directory contains complete, runnable examples demonstrating key features of the PENIN-Ω system.

## Cryptographic Attestation System

### `attestation_integration.py`

Complete end-to-end demonstration of the cryptographic attestation system for model promotions.

**Run it:**
```bash
python examples/attestation_integration.py
```

**What it demonstrates:**
1. Model evaluation by SR-Ω∞ service with cryptographic attestation
2. Gate validation by Σ-Guard service with cryptographic attestation
3. Attestation chain construction and verification
4. Promotion decision based on verified attestation chain
5. Storage of complete cryptographic proof in WORM ledger
6. Independent verification by external auditor

**Output:**
- Console output showing the complete flow
- JSON file with attestation chain: `examples/output/attestation_chain_*.json`

**Key concepts:**
- Ed25519 digital signatures
- Non-repudiation (services cannot deny verdicts)
- Tamper detection (any modification breaks signatures)
- Mathematical verifiability (public-key cryptography)
- Independent audit capability

## Other Examples

More examples will be added as features are developed.

## Requirements

Most examples use direct module loading to avoid dependency issues. They require:
- Python 3.11+
- Standard library only (no additional dependencies)

Some examples may require:
- `cryptography` library (for Ed25519 signatures, recommended)
- If not available, falls back to HMAC-based signatures

## Learn More

- [Attestation Documentation](../docs/attestation.md)
- [Security Guide](../docs/security.md)
- [Architecture Overview](../docs/archive/ENTREGA_COMPLETA_FINAL.md)
