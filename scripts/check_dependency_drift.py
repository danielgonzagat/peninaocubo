#!/usr/bin/env python3
"""
Dependency Drift Checker for PENIN-Ω System.
Checks for version drift between requirements.txt and requirements-lock.txt.
"""

import argparse
import re
import sys
from pathlib import Path


class DependencyDriftChecker:
    """Checks for dependency version drift."""

    def __init__(self, requirements_file: str = "requirements.txt", lock_file: str = "requirements-lock.txt"):
        self.requirements_file = Path(requirements_file)
        self.lock_file = Path(lock_file)
        self.drift_threshold = 0.1  # 10% version difference threshold

    def parse_requirements(self, file_path: Path) -> dict[str, str]:
        """Parse requirements file and extract package versions."""
        packages = {}

        if not file_path.exists():
            return packages

        with open(file_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Parse package specification
                    match = re.match(r"^([a-zA-Z0-9_-]+)([>=<!=]+)(.+)$", line)
                    if match:
                        package_name = match.group(1).lower()
                        operator = match.group(2)
                        version = match.group(3)
                        packages[package_name] = f"{operator}{version}"

        return packages

    def parse_lockfile(self, file_path: Path) -> dict[str, str]:
        """Parse lockfile and extract exact package versions."""
        packages = {}

        if not file_path.exists():
            return packages

        with open(file_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Parse exact version (package==version)
                    if "==" in line:
                        package_name, version = line.split("==", 1)
                        packages[package_name.lower()] = version

        return packages

    def compare_versions(self, req_version: str, lock_version: str) -> tuple[bool, str]:
        """Compare requirement version with lockfile version."""
        # Extract version numbers
        req_match = re.search(r"(\d+\.\d+\.\d+)", req_version)
        lock_match = re.search(r"(\d+\.\d+\.\d+)", lock_version)

        if not req_match or not lock_match:
            return False, "Unable to parse version numbers"

        req_ver = req_match.group(1)
        lock_ver = lock_match.group(1)

        # Compare versions
        [int(x) for x in req_ver.split(".")]
        [int(x) for x in lock_ver.split(".")]

        # Check if lock version satisfies requirement
        if req_version.startswith(">="):
            return lock_ver >= req_ver, f"Lock {lock_ver} vs Req {req_ver}"
        elif req_version.startswith(">"):
            return lock_ver > req_ver, f"Lock {lock_ver} vs Req {req_ver}"
        elif req_version.startswith("<="):
            return lock_ver <= req_ver, f"Lock {lock_ver} vs Req {req_ver}"
        elif req_version.startswith("<"):
            return lock_ver < req_ver, f"Lock {lock_ver} vs Req {req_ver}"
        elif req_version.startswith("=="):
            return lock_ver == req_ver, f"Lock {lock_ver} vs Req {req_ver}"
        else:
            # Default to >= comparison
            return lock_ver >= req_ver, f"Lock {lock_ver} vs Req {req_ver}"

    def check_drift(self) -> dict[str, any]:
        """Check for dependency drift."""
        requirements = self.parse_requirements(self.requirements_file)
        lockfile = self.parse_lockfile(self.lock_file)

        results = {
            "drift_detected": False,
            "missing_in_lock": [],
            "missing_in_requirements": [],
            "version_mismatches": [],
            "summary": {"total_requirements": len(requirements), "total_locked": len(lockfile), "drift_count": 0},
        }

        # Check packages in requirements but not in lockfile
        for package in requirements:
            if package not in lockfile:
                results["missing_in_lock"].append(package)
                results["drift_detected"] = True

        # Check packages in lockfile but not in requirements
        for package in lockfile:
            if package not in requirements:
                results["missing_in_requirements"].append(package)

        # Check version mismatches
        for package in requirements:
            if package in lockfile:
                req_version = requirements[package]
                lock_version = lockfile[package]

                is_compatible, comparison = self.compare_versions(req_version, lock_version)

                if not is_compatible:
                    results["version_mismatches"].append(
                        {
                            "package": package,
                            "requirement": req_version,
                            "locked": lock_version,
                            "comparison": comparison,
                        }
                    )
                    results["drift_detected"] = True

        results["summary"]["drift_count"] = len(results["missing_in_lock"]) + len(results["version_mismatches"])

        return results

    def generate_report(self, results: dict[str, any]) -> str:
        """Generate a human-readable drift report."""
        report = []
        report.append("=" * 60)
        report.append("PENIN-Ω Dependency Drift Report")
        report.append("=" * 60)
        report.append("")

        # Summary
        summary = results["summary"]
        report.append(f"Total Requirements: {summary['total_requirements']}")
        report.append(f"Total Locked: {summary['total_locked']}")
        report.append(f"Drift Issues: {summary['drift_count']}")
        report.append("")

        # Missing in lockfile
        if results["missing_in_lock"]:
            report.append("❌ PACKAGES MISSING IN LOCKFILE:")
            for package in results["missing_in_lock"]:
                report.append(f"  - {package}")
            report.append("")

        # Version mismatches
        if results["version_mismatches"]:
            report.append("⚠️  VERSION MISMATCHES:")
            for mismatch in results["version_mismatches"]:
                report.append(f"  - {mismatch['package']}: {mismatch['comparison']}")
            report.append("")

        # Missing in requirements
        if results["missing_in_requirements"]:
            report.append("ℹ️  PACKAGES IN LOCKFILE BUT NOT IN REQUIREMENTS:")
            for package in results["missing_in_requirements"]:
                report.append(f"  - {package}")
            report.append("")

        # Overall status
        if results["drift_detected"]:
            report.append("🚨 DRIFT DETECTED - ACTION REQUIRED")
            report.append("")
            report.append("Recommended actions:")
            report.append("1. Update requirements.txt with exact versions")
            report.append("2. Regenerate lockfile: pip freeze > requirements-lock.txt")
            report.append("3. Test with updated dependencies")
        else:
            report.append("✅ NO DRIFT DETECTED - DEPENDENCIES ARE IN SYNC")

        return "\n".join(report)

    def fix_drift(self, results: dict[str, any]) -> bool:
        """Attempt to fix detected drift."""
        if not results["drift_detected"]:
            return True

        print("Attempting to fix dependency drift...")

        # Update requirements.txt with exact versions from lockfile
        requirements_path = self.requirements_file
        lockfile_path = self.lock_file

        if not lockfile_path.exists():
            print("❌ Lockfile not found. Cannot fix drift.")
            return False

        # Read current requirements
        with open(requirements_path) as f:
            lines = f.readlines()

        # Update lines with exact versions
        updated_lines = []
        lockfile_packages = self.parse_lockfile(lockfile_path)

        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                # Extract package name
                match = re.match(r"^([a-zA-Z0-9_-]+)", line)
                if match:
                    package_name = match.group(1).lower()
                    if package_name in lockfile_packages:
                        # Replace with exact version
                        exact_version = lockfile_packages[package_name]
                        updated_lines.append(f"{package_name}=={exact_version}\n")
                    else:
                        updated_lines.append(line + "\n")
                else:
                    updated_lines.append(line + "\n")
            else:
                updated_lines.append(line + "\n")

        # Write updated requirements
        with open(requirements_path, "w") as f:
            f.writelines(updated_lines)

        print(f"✅ Updated {requirements_path} with exact versions")
        return True


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Check dependency drift")
    parser.add_argument("--requirements", default="requirements.txt", help="Requirements file path")
    parser.add_argument("--lockfile", default="requirements-lock.txt", help="Lockfile path")
    parser.add_argument("--fix", action="store_true", help="Attempt to fix detected drift")
    parser.add_argument("--threshold", type=float, default=0.1, help="Drift threshold (0.0-1.0)")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()

    checker = DependencyDriftChecker(args.requirements, args.lockfile)
    checker.drift_threshold = args.threshold

    results = checker.check_drift()

    if args.json:
        import json

        print(json.dumps(results, indent=2))
    else:
        report = checker.generate_report(results)
        print(report)

    if args.fix:
        success = checker.fix_drift(results)
        if success:
            print("✅ Drift fix completed")
            sys.exit(0)
        else:
            print("❌ Drift fix failed")
            sys.exit(1)

    # Exit with error code if drift detected
    if results["drift_detected"]:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
