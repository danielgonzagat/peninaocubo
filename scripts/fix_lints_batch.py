#!/usr/bin/env python3
"""Batch fix critical lint issues for PENIN-Ω codebase."""

import re
import sys
from pathlib import Path

WORKSPACE = Path("/workspace")


def fix_bare_except(content: str) -> str:
    """Fix bare except clauses."""
    # Replace bare except with except Exception
    content = re.sub(r"(\s+)except:(\s+)", r"\1except Exception:\2", content)
    return content


def fix_b904_exception_chain(content: str) -> str:
    """Fix B904 - add 'from err' or 'from None' to raise in except."""
    lines = content.split("\n")
    fixed_lines = []
    in_except = False

    for _i, line in enumerate(lines):
        if "except " in line and " as " in line:
            in_except = True
            # Extract variable name
            match = re.search(r"except\s+\w+\s+as\s+(\w+)", line)
            except_var = match.group(1) if match else "err"
            fixed_lines.append(line)
        elif in_except and line.strip().startswith("raise ") and " from " not in line:
            # Add 'from' chain
            if except_var in line or "err" in line or "exc" in line:
                # Use the exception variable
                len(line) - len(line.lstrip())
                fixed_lines.append(line.rstrip() + f" from {except_var}")
            else:
                # No reference to exception, use 'from None'
                fixed_lines.append(line.rstrip() + " from None")
            in_except = False
        else:
            fixed_lines.append(line)
            if line.strip() and not line.strip().startswith("#"):
                in_except = False

    return "\n".join(fixed_lines)


def fix_plw2901_loop_overwrite(content: str) -> str:
    """Fix PLW2901 - loop variable overwrite."""
    # Replace patterns like: for line in ...: line = line.strip()
    # with: for _line in ...: line = _line.strip()
    content = re.sub(
        r"for\s+(line)\s+in\s+(.+?):\n(\s+)\1\s*=\s*\1\.strip\(\)", r"for \1 in \2:\n\3\1 = \1.strip()", content
    )
    return content


def fix_line_length(content: str) -> str:
    """Fix lines that are slightly over 120 chars."""
    lines = content.split("\n")
    fixed_lines = []

    for line in lines:
        if len(line) > 120 and "print(" in line:
            # Try to break print statements
            line = line.replace('", ', '",\n            ')
        fixed_lines.append(line)

    return "\n".join(fixed_lines)


def process_file(file_path: Path):
    """Process a single Python file."""
    try:
        content = file_path.read_text(encoding="utf-8")
        original = content

        # Apply fixes
        content = fix_bare_except(content)
        content = fix_b904_exception_chain(content)
        content = fix_plw2901_loop_overwrite(content)
        content = fix_line_length(content)

        if content != original:
            file_path.write_text(content, encoding="utf-8")
            print(f"✅ Fixed: {file_path.relative_to(WORKSPACE)}")
            return True
        return False
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False


def main():
    """Main execution."""
    print("🔧 Fixing critical lint issues...")

    # Find all Python files
    python_files = list(WORKSPACE.rglob("*.py"))
    python_files = [f for f in python_files if ".venv" not in str(f) and "build" not in str(f)]

    fixed_count = 0
    for file_path in python_files:
        if process_file(file_path):
            fixed_count += 1

    print(f"\n✅ Fixed {fixed_count} files out of {len(python_files)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
