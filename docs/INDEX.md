# 📚 PENIN-Ω Documentation Master Index

**Last Updated**: 2025-10-01  
**Version**: 0.9.0

Welcome to the PENIN-Ω documentation! This index provides quick access to all documentation resources.

---

## 🎯 Quick Start

- **[README.md](../README.md)** — Project overview, features, installation
- **[LEIA_PRIMEIRO.md](../LEIA_PRIMEIRO.md)** — Começar aqui (Português)
- **[CHANGELOG.md](../CHANGELOG.md)** — Release history and changes

---

## 📖 Core Documentation

### Architecture & Design
- **[Architecture Guide](architecture.md)** — System architecture (1100+ lines)
- **[Equations Guide](equations.md)** — Mathematical foundations (15 equations)
- **[Complete System Guide](COMPLETE_SYSTEM_GUIDE.md)** — Comprehensive system overview

### Guides & Tutorials
- **[Setup Guide](SETUP.md)** — Installation and configuration
- **[Equations Complete Guide](guides/PENIN_OMEGA_COMPLETE_EQUATIONS_GUIDE.md)** — Detailed equations tutorial

### Operations
- **Operations Manual** *(Coming Soon)* — Deployment, monitoring, troubleshooting
- **[Hash Algorithm Migration](HASH_ALGORITHM_MIGRATION.md)** — Hash refactoring details
- **[Hash Refactoring Summary](HASH_REFACTORING_SUMMARY.md)** — Hash migration summary

### Ethics & Security
- **[Ethics](ethics.md)** — ΣEA/LO-14 principles and guidelines
- **[Security](security.md)** — Security policies and compliance
- **[Code of Conduct](../CODE_OF_CONDUCT.md)** — Community guidelines

### Contributing
- **[Contributing Guide](../CONTRIBUTING.md)** — How to contribute
- **[Governance](../GOVERNANCE.md)** — Project governance and decision-making

---

## 🧬 Technical References

### Integrations
- **[SOTA Integrations](../penin/integrations/README.md)** — Integration guide and status
- **[NextPy Integration](tests/NEXTPY_INTEGRATION_SUMMARY.md)** — NextPy AMS integration
- **[LLM Providers](guides/llm_providers.md)** — Multi-LLM router configuration

### API Documentation
- **API Reference** *(Coming Soon)* — Full API documentation
- **[Penin Module](../penin/README.md)** *(if exists)* — Core module documentation

---

## 📊 Reports & Analysis

### Current Status
- **[Status Final](../STATUS_FINAL.md)** — Latest project status *(deprecated, will be consolidated)*

### Historical Reports
All historical session reports are archived in:
- **[docs/archive/sessions/](archive/sessions/)** — Past session reports by date

---

## 🔧 Development

### Testing
- **Testing Guide** *(Coming Soon)* — Test suite documentation
- **[Test Reports](tests/)** — Integration test reports

### Tooling
- **[Scripts](../scripts/)** — Utility scripts
- **[Benchmarks](../benchmarks/)** — Performance benchmarks

---

## 📂 Documentation Structure

```
peninaocubo/
├── README.md                  # Project overview
├── CHANGELOG.md               # Release notes
├── CONTRIBUTING.md            # How to contribute
├── GOVERNANCE.md              # Project governance
├── CODE_OF_CONDUCT.md         # Community guidelines
├── SECURITY.md                # Security policies
├── LEIA_PRIMEIRO.md           # Quick start (PT-BR)
│
├── docs/                      # Current documentation
│   ├── INDEX.md               # This file
│   ├── architecture.md        # System architecture
│   ├── equations.md           # Mathematical foundations
│   ├── ethics.md              # Ethics and principles
│   ├── security.md            # Security documentation
│   ├── guides/                # Tutorials and guides
│   ├── tests/                 # Test documentation
│   ├── reports/               # Current reports
│   └── archive/               # Historical documentation
│       └── sessions/          # Archived session reports
│
└── penin/                     # Source code
    ├── integrations/README.md # Integration guide
    └── ... (source modules)
```

---

## 🔗 External Resources

- **[GitHub Repository](https://github.com/danielgonzagat/peninaocubo)**
- **[GitHub Issues](https://github.com/danielgonzagat/peninaocubo/issues)**
- **[GitHub Discussions](https://github.com/danielgonzagat/peninaocubo/discussions)**

---

## 📝 Documentation Guidelines

When adding new documentation:

1. **Place appropriately**:
   - Core concepts → `docs/`
   - Guides/tutorials → `docs/guides/`
   - Session reports → `docs/archive/sessions/YYYY-MM-DD/`

2. **Update this index** when adding major documentation

3. **Follow naming conventions**:
   - Use lowercase with underscores: `my_guide.md`
   - Date-based: `YYYY-MM-DD-report.md`
   - Descriptive names

4. **Include metadata**:
   ```markdown
   # Document Title
   **Date**: YYYY-MM-DD  
   **Version**: X.Y.Z  
   **Status**: Draft/Review/Final
   ```

---

## 🆘 Need Help?

- **Issues**: Report bugs or request features on [GitHub Issues](https://github.com/danielgonzagat/peninaocubo/issues)
- **Discussions**: Ask questions on [GitHub Discussions](https://github.com/danielgonzagat/peninaocubo/discussions)
- **Email**: contact@example.com

---

**Last Updated**: 2025-10-01  
**Maintained by**: PENIN-Ω Contributors  
**License**: Apache 2.0
