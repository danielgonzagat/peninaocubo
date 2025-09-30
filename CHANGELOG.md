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

## [0.8.0] — 2025-01-30
### Added
- CLI `penin` via `pyproject.toml` (entry‑point) para operar o sistema.
- Testes novos: unicidade de `phi_caos`, sintaxe do router e HMAC do L2.
- Tooling de segurança e qualidade: pre‑commit (ruff/black/mypy) e gitleaks (CI).
- Cache L2 com integridade HMAC (SHA‑256) usando orjson.
- Arquivo `.env.example` com variáveis de ambiente necessárias.
- Licença Apache-2.0.

### Changed
- `requirements.txt` deduplicado e organizado por áreas, com orientação de lockfile.
- Router consolidado para um único tracker de orçamento diário (file‑backed usage).
- Cache L2 migrado de `pickle` para `orjson + HMAC` para segurança.

### Fixed
- Remoção de duplicidade de `phi_caos` em `penin/omega/caos.py`.
- Consolidação de classes duplicadas em `caos.py`.

### Security
- Cache L2 com verificação de integridade HMAC (SHA‑256).
- Prevenção de tampering de dados em cache.
- Workflow de segurança com gitleaks para detecção de segredos.

---

## [0.7.1] — 2025-01-29
### Added
- Métricas éticas computadas (ECE, ρ-bias, Fairness Score).
- Endpoint /metrics seguro com bind em 127.0.0.1.
- WORM com WAL + busy_timeout para concorrência.
- Router cost-aware com orçamento diário e tracking automático.
- Observabilidade completa com Prometheus + JSON logs.
- League Service (Shadow/Canary) com rollback automático.

### Security
- Comportamento fail-closed por default.
- Auditabilidade completa com WORM e hash chain.
- Determinismo garantido com seed state rastreável.

---

[Unreleased]: https://github.com/danielgonzagat/peninaocubo/compare/v0.8.0...HEAD
[0.8.0]: https://github.com/danielgonzagat/peninaocubo/releases/tag/v0.8.0
[0.7.1]: https://github.com/danielgonzagat/peninaocubo/releases/tag/v0.7.1