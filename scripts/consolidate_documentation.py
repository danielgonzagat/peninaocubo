#!/usr/bin/env python3
"""
Documentation Consolidation Script
===================================

Consolidates 166 markdown files into organized structure:
- Root: Only essential files (README, CHANGELOG, LICENSE, CONTRIBUTING)
- docs/: Current documentation
- docs/archive/sessions/: Historical session reports

Target: 166 → ~50 files
"""

import shutil
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# Files to KEEP in root (essential only)
ROOT_ESSENTIAL = {
    "README.md",
    "CHANGELOG.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "GOVERNANCE.md",
    "SECURITY.md",
    "LEIA_PRIMEIRO.md",
    ".gitignore",
    ".gitattributes",
    "pyproject.toml",
    "requirements.txt",
    "pytest.ini",
    "mkdocs.yml",
    ".env.example",
    ".flake8",
    ".pre-commit-config.yaml",
}

# Status/report files to archive (move to docs/archive/sessions/YYYY-MM-DD/)
STATUS_REPORTS_PATTERN = [
    "*ANALISE*.md",
    "*STATUS*.md",
    "*RELATORIO*.md",
    "*REPORT*.md",
    "*SUMMARY*.md",
    "*TRANSFORMACAO*.md",
    "*TRANSFORMATION*.md",
    "*ENTREGA*.md",
    "*SESSAO*.md",
    "*CONSOLIDACAO*.md",
    "*IMPLEMENTATION*.md",
    "*OPTIMIZATION*.md",
    "*EXECUTIVE*.md",
    "*MISSAO*.md",
    "*PLANO*.md",
    "*PROXIMO*.md",
    "*RESUMO*.md",
    "*INDEX_DOCUMENTACAO*.md",
]

# Documentation to keep in docs/ (current)
DOCS_CURRENT = {
    "docs/architecture.md",
    "docs/equations.md",
    "docs/ethics.md",
    "docs/security.md",
    "docs/COMPLETE_SYSTEM_GUIDE.md",
    "docs/SETUP.md",
    "docs/HASH_ALGORITHM_MIGRATION.md",
    "docs/HASH_REFACTORING_SUMMARY.md",
}


def find_status_reports() -> list[Path]:
    """Find all status/report markdown files in root."""
    reports = []
    for pattern in STATUS_REPORTS_PATTERN:
        reports.extend(PROJECT_ROOT.glob(pattern))

    # Filter to only .md files in root (not subdirectories)
    root_reports = [f for f in reports if f.parent == PROJECT_ROOT and f.suffix == ".md"]

    # Exclude essential files
    root_reports = [f for f in root_reports if f.name not in ROOT_ESSENTIAL]

    return sorted(set(root_reports))


def create_archive_session_dir() -> Path:
    """Create docs/archive/sessions/YYYY-MM-DD/ directory."""
    session_date = datetime.now().strftime("%Y-%m-%d")
    archive_dir = PROJECT_ROOT / "docs" / "archive" / "sessions" / session_date
    archive_dir.mkdir(parents=True, exist_ok=True)
    return archive_dir


def move_to_archive(file_path: Path, archive_dir: Path, dry_run: bool = True) -> bool:
    """Move file to archive directory."""
    if not file_path.exists():
        return False

    dest_path = archive_dir / file_path.name

    if dry_run:
        print(f"📦 Would archive: {file_path.name}")
        print(f"   → {dest_path.relative_to(PROJECT_ROOT)}")
    else:
        try:
            shutil.move(str(file_path), str(dest_path))
            print(f"✅ Archived: {file_path.name} → {dest_path.relative_to(PROJECT_ROOT)}")
            return True
        except Exception as e:
            print(f"⚠️  Error archiving {file_path.name}: {e}")
            return False

    return True


def create_master_index(dry_run: bool = True):
    """Create master documentation index at docs/INDEX.md."""
    index_content = """# 📚 PENIN-Ω Documentation Master Index

**Last Updated**: {date}
**Version**: {version}

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

**Last Updated**: {date}
**Maintained by**: PENIN-Ω Contributors
**License**: Apache 2.0
"""

    index_path = PROJECT_ROOT / "docs" / "INDEX.md"

    # Format with current date and version
    from datetime import datetime
    formatted_content = index_content.format(
        date=datetime.now().strftime("%Y-%m-%d"),
        version="0.9.0"  # TODO: Read from pyproject.toml
    )

    if dry_run:
        print(f"\n📝 Would create master index: {index_path.relative_to(PROJECT_ROOT)}")
    else:
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(formatted_content)
        print(f"\n✅ Created master index: {index_path.relative_to(PROJECT_ROOT)}")


def consolidate_documentation(dry_run: bool = True):
    """Main consolidation function."""
    print("=" * 70)
    print("PENIN-Ω Documentation Consolidation")
    print("=" * 70)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print()

    # Step 1: Find status reports
    print("📁 Finding status/report files in root...")
    reports = find_status_reports()
    print(f"   Found {len(reports)} report files to archive")
    print()

    # Step 2: Create archive directory
    print("📦 Creating archive directory...")
    archive_dir = create_archive_session_dir()
    print(f"   Archive: {archive_dir.relative_to(PROJECT_ROOT)}")
    print()

    # Step 3: Move reports to archive
    print("📦 Archiving reports...")
    archived_count = 0
    for report in reports:
        if move_to_archive(report, archive_dir, dry_run=dry_run):
            archived_count += 1
    print(f"   Archived: {archived_count} files")
    print()

    # Step 4: Create master index
    print("📝 Creating master documentation index...")
    create_master_index(dry_run=dry_run)
    print()

    # Summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Reports archived: {archived_count}")
    print(f"Archive location: {archive_dir.relative_to(PROJECT_ROOT)}")
    print("Master index: docs/INDEX.md")

    if dry_run:
        print()
        print("ℹ️  This was a DRY RUN. No changes were made.")
        print("   Run with --live to apply changes.")
    else:
        print()
        print("✅ Documentation consolidation complete!")
        print()
        print("Next steps:")
        print("  1. Review archived files")
        print("  2. Update README.md to reference docs/INDEX.md")
        print("  3. Commit changes")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Consolidate documentation structure")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Apply changes (default: dry-run only)"
    )

    args = parser.parse_args()

    consolidate_documentation(dry_run=not args.live)
