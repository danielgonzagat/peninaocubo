# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/), e este projeto adota [SemVer](https://semver.org/lang/pt-BR/).

## [Unreleased]
### Added
- (planejado) OPA/Rego para Σ‑Guard e IR→IC (P2).
- (planejado) Pipeline de release assinado e SBOM (P3).

### Changed
- (planejado) Separação dos modos CAOS⁺ (explore vs promote).

### Security
- (planejado) Observabilidade externa segura (Nginx+TLS+Auth+IP allowlist).

---

## [0.8.0] — 2025-09-30
### Added
- CLI `penin` via `pyproject.toml` (entry‑point) para operar o sistema.
- Testes novos: unicidade de `phi_caos`, sintaxe do router e HMAC do L2.
- Tooling de segurança e qualidade: pre‑commit (ruff/black/mypy) e gitleaks (CI).

### Changed
- `requirements.txt` deduplicado e organizado por áreas, com orientação de lockfile.
- Router consolidado para um único tracker de orçamento diário (file‑backed usage).

### Fixed
- Remoção de duplicidade de `phi_caos` em `penin/omega/caos.py`.

### Security
- Cache L2 migrado de `pickle` para `orjson + HMAC (SHA‑256)` com verificação de integridade.

[Unreleased]: https://example.com/compare/v0.8.0...HEAD
[0.8.0]: https://example.com/releases/tag/v0.8.0