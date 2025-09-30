# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/), e este projeto adota [SemVer](https://semver.org/lang/pt-BR/).

## [Unreleased]
### Added
- (planejado) OPA/Rego para Σ-Guard e IR→IC (P2).
- (planejado) Pipeline de release assinado e SBOM (P3).

### Changed
- (planejado) Separação dos modos CAOS⁺ (explore vs promote).

### Security
- (planejado) Observabilidade externa segura (Nginx + TLS + Auth + allowlist).

---

## [0.8.0] — 2025-09-30
### Added
- CLI `penin` via `pyproject.toml` com entry-point publicado.
- Novos testes para CAOS, router e cache L2 com HMAC.
- Tooling de segurança e qualidade: pre-commit (ruff/black/mypy) e gitleaks (workflow dedicado).

### Changed
- `requirements.txt` deduplicado e organizado com instruções de lockfile.
- Router consolidado com rastreamento de orçamento persistente e sensível a custo.

### Fixed
- Remoção da duplicidade de `phi_caos` em `penin/omega/caos.py`.

### Security
- Cache L2 migrado de `pickle` para `orjson + HMAC (SHA-256)` com verificação de integridade.

[Unreleased]: https://github.com/danielgonzagat/peninaocubo/compare/v0.8.0...HEAD
[0.8.0]: https://github.com/danielgonzagat/peninaocubo/releases/tag/v0.8.0
