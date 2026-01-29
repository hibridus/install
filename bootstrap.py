import sys
import json
import shutil
import subprocess
import requests
from pathlib import Path

# BSD 2-Clause License
# 
# Copyright (c) 2026, Hibridus source code
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# This python script serves only to perform a setup before
# running the Hibridus installation.
# If you have any questions, please read 
# https://github.com/hibridus/docs/BOOTSTRAP.md

REQUIRED_PACKAGES = ["xorriso", "nasm", "clang"]

def abort():
    print("! Setup stopped due an error.")
    sys.exit(1)

def is_installed(program):
    # Check if a program exists in PATH
    return shutil.which(program) is not None

def get_install_manager():
    # Cache detected manager to avoid re-checking because
    # Python sucks
    manager = getattr(get_install_manager, "manager", None)
    if manager:
        return manager

    for manager in ("dnf", "apk", "apt", "pacman", "zypper"):
        if is_installed(manager):
            get_install_manager.manager = manager
            return manager

    print("""
! No standard package manager found.
! Please read https://github.com/hibridus/docs/BOOTSTRAP.md
! to more info.
""")
    abort()

def install_package(manager, pkg):
    # Command templates for each package manager
    templates = {
        "apt": ["sudo", "apt", "install", "-y", "{pkg}"],
        "dnf": ["sudo", "dnf", "install", "-y", "{pkg}"],
        "pacman": ["sudo", "pacman", "-S", "--noconfirm", "{pkg}"],
        "zypper": ["sudo", "zypper", "install", "-y", "{pkg}"],
        "apk": ["sudo", "apk", "add", "{pkg}"]
    }

    cmd = [arg.format(pkg=pkg) for arg in templates[manager]]
    print(f"! Installing {pkg}...")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        print(f"! Failed to install {pkg} with command: {' '.join(cmd)}")
        abort()

def checkup_and_install(manager):
    # Cache results to avoid multiple PATH lookups
    status_map = {pkg: is_installed(pkg) for pkg in REQUIRED_PACKAGES}

    for pkg, ok in status_map.items():
        print(f"! {pkg} -> {'SATISFIED' if ok else 'NOT INSTALLED'}")

    for pkg, ok in status_map.items():
        if not ok: install_package(manager, pkg)

def is_hibridus_installed():
    return Path("VERSION/VERSION.md").is_file()

def get_installed_version():
    try:
        return Path("VERSION/VERSION.md").read_text().strip()
    except FileNotFoundError:
        return None

def get_remote_version():
    url = "https://raw.githubusercontent.com/hibridus/VERSION/main/VERSION.md"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return r.text.strip()
    except:
        return None

def load_cache():
    try:
        with open(Path("cache/repos.json")) as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()

def save_cache(repos):
    Path("cache/repos.json").parent.mkdir(exist_ok=True)
    with open(Path("cache/repos.json"), "w") as f:
        json.dump(sorted(repos), f, indent=2)

def get_repositories():
    url = f"https://api.github.com/orgs/{"hibridus"}/repos"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return [repo["name"] for repo in r.json()]
    except Exception:
        print("! Failed to fetch repositories from GitHub.")
        abort()

def parse_repo_name(name):
    # Split repo name into base and submodule
    # foo_bar_xyz -> ("foo", "bar_xyz")
    base, *rest = name.split("_", 1)
    return base, rest[0] if rest else None

def clone_repo(repo):
    base, sub = parse_repo_name(repo)
    target = Path(base) / sub if sub else Path(base)

    target.parent.mkdir(parents=True, exist_ok=True)

    if target.is_dir():
        print(f"! Skipping {repo}, directory already exists.")
        return True

    print(f"! Cloning {repo} into {target}")
    try:
        subprocess.run(
            ["git", "clone", f"https://github.com/{"hibridus"}/{repo}.git", str(target), "--depth=1"],
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        print(f"! Failed to clone {repo}")
        abort()

def sync_repositories():
    print("Syncing GitHub repositories...")

    cached = load_cache()
    repos = get_repositories()
    new_cache = set(cached)

    for repo in repos:
        if repo == "install": # To not sync this script
            continue
        
        if repo in cached:
            print(f"! {repo} already cached, skipping.")
            continue

        if clone_repo(repo):
            new_cache.add(repo)

    if new_cache != cached:
        save_cache(new_cache)

    print("Repository sync done.")

def main():
    print("Getting installation info...")
    manager = get_install_manager()
    print(f"! Using `{manager}` as the package manager.")
    checkup_and_install(manager)

    print("Checking system source code...")

    if not is_hibridus_installed():
        print("! Hibridus not detected.")
        print("! Starting fresh installation...")
        sync_repositories()
        
        print("Mounting JSON...")
        
        try:
            Path("cache/config.json").write_text(
"""{
    "COMPILER": "clang",
    "FLAGS": "-O2 -ffreestanding -fno-stack-protector -fno-pic -fno-pie -mno-red-zone -mcmodel=kernel -nostdlib -fno-builtin -fno-unwind-tables -fno-asynchronous-unwind-tables",
    "TARGET": "x86-64-elf"
}""")
        except:
            print("! Failed to create JSON file")
    
        print("! JSON mounted in cache/config.json\n" + Path("cache/config.json").read_text())
    else:
        version = get_installed_version()
        print(f"! Hibridus alredy installed.")
        print(f"! Installed version: {version}")
        print("Checking for updates...")
        
        remote_version = get_remote_version()
        if not version == remote_version:
            print(f"! The installed version {version} not synchronized.")
            sync_repositories()
    
    print("Setupping Limine...")
    subprocess.run(["./limine/bootstrap"], check=True)
    subprocess.run(["./limine/configure", "--prefix=$PREFIX", "--enable-bios"], check=True)
    subprocess.run(["make", "install"], check=True)
    
    print("Installation done successfully.")


if __name__ == "__main__":
    main()
    sys.exit(0)