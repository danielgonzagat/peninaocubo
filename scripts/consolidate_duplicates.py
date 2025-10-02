#!/usr/bin/env python3
"""
Consolidation Script — Remove Code Duplicates Safely
====================================================

This script removes duplicate implementations identified in the analysis,
updating all imports to point to canonical locations.

Phase 1: Consolidation
- CAOS+: Deprecate old implementations
- L∞: Consolidate to penin/math/linf.py
- WORM: Consolidate ledger implementations
- Router: Consolidate structure

Safety:
- Dry-run mode by default
- Git backup recommended
- Test suite must pass after changes
"""

import re
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Duplicates map: old_path -> canonical_path
DUPLICATES_TO_REMOVE = {
    # CAOS+ duplicates (keep only penin/core/caos.py)
    "penin/equations/caos_plus.py": "penin/core/caos.py",
    "penin/math/caos_plus_complete.py": "penin/core/caos.py",
    # Note: penin/engine/caos_plus.py is a deprecation wrapper, keep for compatibility

    # L∞ duplicates (keep only penin/math/linf.py)
    "penin/equations/linf_meta.py": "penin/math/linf.py",
}

# Import mappings: old_import -> new_import
IMPORT_MAPPINGS = {
    # CAOS+
    "from penin.core.caos import": "from penin.core.caos import",
    "import penin.core.caos": "import penin.core.caos",

    # L∞
    "from penin.math.linf import": "from penin.math.linf import",
    "import penin.math.linf": "import penin.math.linf",
}

# Function/class renames if needed
SYMBOL_RENAMES: dict[str, str] = {
    # Example: "old_function_name": "new_function_name"
}


def find_python_files(exclude_patterns: list[str] = None) -> list[Path]:
    """Find all Python files in project."""
    if exclude_patterns is None:
        exclude_patterns = [
            "*/venv/*", "*/.venv/*", "*/node_modules/*",
            "*/build/*", "*/dist/*", "*/__pycache__/*",
            "*/docs/archive/*"
        ]

    python_files = []
    for py_file in PROJECT_ROOT.rglob("*.py"):
        # Check if file matches any exclude pattern
        if any(py_file.match(pattern) for pattern in exclude_patterns):
            continue
        python_files.append(py_file)

    return python_files


def find_imports_in_file(file_path: Path) -> set[str]:
    """Extract all import statements from a Python file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Use regex to find imports (simple approach)
        import_pattern = re.compile(r'^(from .+ import .+|import .+)$', re.MULTILINE)
        imports = set(import_pattern.findall(content))
        return imports
    except Exception as e:
        print(f"⚠️  Error reading {file_path}: {e}")
        return set()


def update_imports_in_file(file_path: Path, dry_run: bool = True) -> int:
    """Update imports in a file according to IMPORT_MAPPINGS."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        changes = 0

        # Apply import mappings
        for old_import, new_import in IMPORT_MAPPINGS.items():
            if old_import in content:
                content = content.replace(old_import, new_import)
                changes += 1

        # Apply symbol renames
        for old_symbol, new_symbol in SYMBOL_RENAMES.items():
            # Be careful: only rename function calls, not inside strings
            # Simple approach: regex for word boundaries
            pattern = rf'\b{re.escape(old_symbol)}\b'
            if re.search(pattern, content):
                content = re.sub(pattern, new_symbol, content)
                changes += 1

        if changes > 0:
            if dry_run:
                print(f"✏️  Would update {file_path} ({changes} changes)")
            else:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"✅ Updated {file_path} ({changes} changes)")

        return changes

    except Exception as e:
        print(f"⚠️  Error processing {file_path}: {e}")
        return 0


def deprecate_file(file_path: Path, canonical_path: str, dry_run: bool = True):
    """Add deprecation notice to a file."""
    deprecation_notice = f'''"""
DEPRECATED: {file_path.relative_to(PROJECT_ROOT)}
{'=' * 70}

This module has been CONSOLIDATED into {canonical_path}.

Maintained only for backward compatibility.
All new development should use:

    from {canonical_path.replace('/', '.').replace('.py', '')} import ...

This file will be removed in version 2.0.0.

Migration:
----------
Update all imports from this module to use the canonical location above.
"""

# Import from canonical location for compatibility
try:
    from {canonical_path.replace('/', '.').replace('.py', '')} import *
except ImportError:
    pass
'''

    if dry_run:
        print(f"📝 Would deprecate {file_path}")
        print(f"   → Canonical: {canonical_path}")
    else:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(deprecation_notice)
        print(f"✅ Deprecated {file_path}")


def remove_file(file_path: Path, dry_run: bool = True):
    """Remove a file (only if dry_run=False)."""
    if dry_run:
        print(f"🗑️  Would remove {file_path}")
    else:
        file_path.unlink()
        print(f"✅ Removed {file_path}")


def consolidate_duplicates(dry_run: bool = True, mode: str = "deprecate"):
    """
    Main consolidation function.

    Args:
        dry_run: If True, only print what would be done
        mode: "deprecate" (add deprecation notice) or "remove" (delete file)
    """
    print("=" * 70)
    print("PENIN-Ω Code Consolidation Script")
    print("=" * 70)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Action: {mode.upper()}")
    print()

    # Step 1: Find all Python files
    print("📁 Finding Python files...")
    python_files = find_python_files()
    print(f"   Found {len(python_files)} Python files")
    print()

    # Step 2: Update imports in all files
    print("🔄 Updating imports...")
    total_changes = 0
    for py_file in python_files:
        changes = update_imports_in_file(py_file, dry_run=dry_run)
        total_changes += changes
    print(f"   Total import updates: {total_changes}")
    print()

    # Step 3: Handle duplicate files
    print(f"🗂️  Handling duplicate files ({mode})...")
    for old_path_str, canonical_path in DUPLICATES_TO_REMOVE.items():
        old_path = PROJECT_ROOT / old_path_str
        if old_path.exists():
            if mode == "deprecate":
                deprecate_file(old_path, canonical_path, dry_run=dry_run)
            elif mode == "remove":
                remove_file(old_path, dry_run=dry_run)
        else:
            print(f"⚠️  File not found: {old_path}")
    print()

    # Summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Import updates: {total_changes}")
    print(f"Duplicate files handled: {len(DUPLICATES_TO_REMOVE)}")

    if dry_run:
        print()
        print("ℹ️  This was a DRY RUN. No changes were made.")
        print("   Run with --live to apply changes.")
    else:
        print()
        print("✅ Consolidation complete!")
        print("   Next step: Run tests to verify nothing broke.")
        print("   Command: pytest tests/ -v")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Consolidate duplicate code implementations")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Apply changes (default: dry-run only)"
    )
    parser.add_argument(
        "--mode",
        choices=["deprecate", "remove"],
        default="deprecate",
        help="How to handle duplicates: deprecate (add notice) or remove (delete)"
    )

    args = parser.parse_args()

    consolidate_duplicates(dry_run=not args.live, mode=args.mode)
