#!/usr/bin/env python3
"""
Dependency Updater for PENIN-Ω System.
Automatically updates dependencies while maintaining compatibility.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


class DependencyUpdater:
    """Updates project dependencies safely."""

    def __init__(self, requirements_file: str = "requirements.txt"):
        self.requirements_file = Path(requirements_file)
        self.backup_file = Path(f"{requirements_file}.backup")
        self.test_results = {}

    def backup_requirements(self):
        """Create backup of current requirements."""
        if self.requirements_file.exists():
            with open(self.requirements_file) as src:
                with open(self.backup_file, "w") as dst:
                    dst.write(src.read())
            print(f"✅ Backed up requirements to {self.backup_file}")

    def get_outdated_packages(self) -> list[dict[str, str]]:
        """Get list of outdated packages."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--outdated", "--format=json"],
                capture_output=True,
                text=True,
                check=True,
            )

            outdated = json.loads(result.stdout)
            return outdated
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            print(f"❌ Error getting outdated packages: {e}")
            return []

    def get_security_vulnerabilities(self) -> list[dict[str, str]]:
        """Check for security vulnerabilities."""
        try:
            # Try to use safety if available
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "safety"], check=False, capture_output=True, text=True
            )

            result = subprocess.run(
                [sys.executable, "-m", "safety", "check", "--json"], check=False, capture_output=True, text=True
            )

            if result.returncode == 0:
                vulnerabilities = json.loads(result.stdout)
                return vulnerabilities
            else:
                print("⚠️  Safety check failed or no vulnerabilities found")
                return []
        except Exception as e:
            print(f"⚠️  Could not check security vulnerabilities: {e}")
            return []

    def update_package(self, package_name: str, target_version: str | None = None) -> bool:
        """Update a single package."""
        try:
            if target_version:
                cmd = [sys.executable, "-m", "pip", "install", f"{package_name}=={target_version}"]
            else:
                cmd = [sys.executable, "-m", "pip", "install", "--upgrade", package_name]

            subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"✅ Updated {package_name}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to update {package_name}: {e.stderr}")
            return False

    def test_updated_dependencies(self) -> bool:
        """Run tests to verify updated dependencies work."""
        print("🧪 Testing updated dependencies...")

        test_commands = [
            [sys.executable, "-c", 'import penin.omega.caos; print("CAOS import OK")'],
            [sys.executable, "-c", 'import penin.router; print("Router import OK")'],
            [sys.executable, "-c", 'import penin.policies; print("Policies import OK")'],
        ]

        all_passed = True
        for cmd in test_commands:
            try:
                subprocess.run(cmd, capture_output=True, text=True, check=True)
                print(f"✅ {cmd[-1]}")
            except subprocess.CalledProcessError as e:
                print(f"❌ {cmd[-1]}: {e.stderr}")
                all_passed = False

        return all_passed

    def update_requirements_file(self, updated_packages: dict[str, str]):
        """Update requirements.txt with new versions."""
        if not self.requirements_file.exists():
            print("❌ Requirements file not found")
            return False

        # Read current requirements
        with open(self.requirements_file) as f:
            lines = f.readlines()

        # Update lines with new versions
        updated_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                # Extract package name
                package_name = line.split(">=")[0].split("==")[0].split(">")[0].split("<")[0].split("!=")[0]
                if package_name in updated_packages:
                    # Update with new version
                    new_version = updated_packages[package_name]
                    updated_lines.append(f"{package_name}>={new_version}\n")
                else:
                    updated_lines.append(line + "\n")
            else:
                updated_lines.append(line + "\n")

        # Write updated requirements
        with open(self.requirements_file, "w") as f:
            f.writelines(updated_lines)

        print(f"✅ Updated {self.requirements_file}")
        return True

    def generate_lockfile(self):
        """Generate new lockfile."""
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True, check=True)

            with open("requirements-lock.txt", "w") as f:
                f.write(result.stdout)

            print("✅ Generated new lockfile")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to generate lockfile: {e}")
            return False

    def rollback(self):
        """Rollback to backup if update failed."""
        if self.backup_file.exists():
            with open(self.backup_file) as src:
                with open(self.requirements_file, "w") as dst:
                    dst.write(src.read())
            print("🔄 Rolled back to backup")

    def update_dependencies(
        self, update_all: bool = False, security_only: bool = False, test_after_update: bool = True
    ) -> bool:
        """Main update process."""
        print("🔍 Checking for outdated packages...")

        # Backup current requirements
        self.backup_requirements()

        # Get outdated packages
        outdated = self.get_outdated_packages()
        if not outdated:
            print("✅ All packages are up to date")
            return True

        # Get security vulnerabilities
        vulnerabilities = self.get_security_vulnerabilities()
        vulnerable_packages = {v.get("package", "").lower() for v in vulnerabilities}

        # Filter packages to update
        packages_to_update = []
        if security_only:
            packages_to_update = [p for p in outdated if p["name"].lower() in vulnerable_packages]
        elif update_all:
            packages_to_update = outdated
        else:
            # Update only packages with security vulnerabilities by default
            packages_to_update = [p for p in outdated if p["name"].lower() in vulnerable_packages]

        if not packages_to_update:
            print("✅ No packages need updating")
            return True

        print(f"📦 Found {len(packages_to_update)} packages to update:")
        for pkg in packages_to_update:
            print(f"  - {pkg['name']}: {pkg['version']} → {pkg['latest_version']}")

        # Update packages
        updated_packages = {}
        update_success = True

        for pkg in packages_to_update:
            package_name = pkg["name"]
            latest_version = pkg["latest_version"]

            if self.update_package(package_name, latest_version):
                updated_packages[package_name] = latest_version
            else:
                update_success = False

        if not update_success:
            print("❌ Some packages failed to update")
            return False

        # Test updated dependencies
        if test_after_update:
            if not self.test_updated_dependencies():
                print("❌ Tests failed after update, rolling back...")
                self.rollback()
                return False

        # Update requirements file
        if updated_packages:
            self.update_requirements_file(updated_packages)
            self.generate_lockfile()

        print("✅ Dependency update completed successfully")
        return True


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Update project dependencies")
    parser.add_argument("--all", action="store_true", help="Update all outdated packages")
    parser.add_argument(
        "--security-only", action="store_true", help="Update only packages with security vulnerabilities"
    )
    parser.add_argument("--no-test", action="store_true", help="Skip testing after update")
    parser.add_argument("--requirements", default="requirements.txt", help="Requirements file path")

    args = parser.parse_args()

    updater = DependencyUpdater(args.requirements)

    success = updater.update_dependencies(
        update_all=args.all, security_only=args.security_only, test_after_update=not args.no_test
    )

    if success:
        print("🎉 Dependency update completed successfully!")
        sys.exit(0)
    else:
        print("💥 Dependency update failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
