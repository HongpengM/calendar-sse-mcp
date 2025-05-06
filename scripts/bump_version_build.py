#!/usr/bin/env python3
"""
Script to bump the version in pyproject.toml, clear the dist/ directory, and build the package.

By default, bumps the patch version (e.g., 0.1.7 -> 0.1.8).
Use --minor to bump minor version (e.g., 0.1.7 -> 0.2.0)
Use --major to bump major version (e.g., 0.1.7 -> 1.0.0)
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Get the project root directory
script_dir = Path(__file__).parent
project_root = script_dir.parent

# Path to the pyproject.toml file
pyproject_path = project_root / "pyproject.toml"
# Path to the __init__.py file
init_path = project_root / "src" / "calendar_sse_mcp" / "__init__.py"

def bump_version(bump_type="patch"):
    """Bump the version in pyproject.toml
    
    Args:
        bump_type: Type of version bump ('patch', 'minor', or 'major')
    """
    # Read the pyproject.toml file
    with open(pyproject_path, "r") as f:
        content = f.read()
    
    # Find the version line with a regex pattern
    version_pattern = re.compile(r'version\s*=\s*"(\d+)\.(\d+)\.(\d+)"')
    match = version_pattern.search(content)
    
    if not match:
        print("Version pattern not found in pyproject.toml")
        return False
    
    # Extract the version components
    major, minor, patch = map(int, match.groups())
    
    # Increment version based on bump_type
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    else:  # patch (default)
        patch += 1
    
    # Format the new version
    new_version = f"{major}.{minor}.{patch}"
    
    # Replace the version in the file content
    new_content = version_pattern.sub(f'version = "{new_version}"', content)
    
    # Write the updated content back to the file
    with open(pyproject_path, "w") as f:
        f.write(new_content)
    
    # Also update the version in __init__.py
    update_init_version(new_version)
    
    old_version = ".".join(match.groups())
    print(f"Version updated: {old_version} -> {new_version}")
    return new_version

def update_init_version(new_version):
    """Update the __version__ in __init__.py
    
    Args:
        new_version: New version string
    """
    # Check if __init__.py exists
    if not init_path.exists():
        print(f"Warning: {init_path} does not exist, cannot update __version__")
        return
    
    # Read the current __init__.py
    with open(init_path, "r") as f:
        init_content = f.read()
    
    # Replace the version line
    version_pattern = re.compile(r'__version__\s*=\s*"[^"]+"')
    new_init_content = version_pattern.sub(f'__version__ = "{new_version}"', init_content)
    
    # Write back the updated content
    with open(init_path, "w") as f:
        f.write(new_init_content)
    
    print(f"Updated __version__ in {init_path}")

def clear_dist_directory():
    """Clear the dist/ directory"""
    dist_dir = project_root / "dist"
    
    if dist_dir.exists():
        print(f"Clearing dist directory: {dist_dir}")
        shutil.rmtree(dist_dir)
        os.makedirs(dist_dir)
        print("Dist directory cleared and recreated")
    else:
        print("Dist directory not found, creating it")
        os.makedirs(dist_dir)

def build_package():
    """Build the package using uv"""
    print("Building package with uv...")
    try:
        subprocess.run(["uv", "build"], cwd=project_root, check=True)
        print("Build completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error during build: {e}")
        return False

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Bump version, clear dist/ directory, and build package")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--patch", action="store_true", default=True, help="Bump patch version (default)")
    group.add_argument("--minor", action="store_true", help="Bump minor version")
    group.add_argument("--major", action="store_true", help="Bump major version")
    args = parser.parse_args()
    
    # Determine which version component to bump
    if args.major:
        bump_type = "major"
    elif args.minor:
        bump_type = "minor"
    else:
        bump_type = "patch"
    
    # Step 1: Bump the version
    new_version = bump_version(bump_type)
    if not new_version:
        sys.exit(1)
    
    # Step 2: Clear the dist directory
    clear_dist_directory()
    
    # Step 3: Build the package
    success = build_package()
    
    if success:
        print(f"Successfully bumped version to {new_version} and built the package")
        print(f"Distribution files created in {project_root}/dist/")
    else:
        print("Failed to complete the build process")
        sys.exit(1)

if __name__ == "__main__":
    main() 