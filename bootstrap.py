import sys
import os
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

REQUIRED_PACKAGES = ["xorriso", "nasm", "clang", "automake", "lld", "llvm"]

ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT / "src"
CACHE_DIR = ROOT / "cache"

CONFIG_JSON = CACHE_DIR / "config.json"
REPOS_CACHE = CACHE_DIR / "repos.json"
VERSION_FILE = ROOT / "VERSION/VERSION.md"

VERSION_URL = "https://raw.githubusercontent.com/hibridus/VERSION/main/VERSION.md"
REPOS_API = "https://api.github.com/orgs/hibridus/repos"

def abort(msg="Setup stopped due an error."):
    print(f"! {msg}")
    sys.exit(1)

def run(cmd, **kw):
    try:
        subprocess.run(cmd, check=True, **kw)
    except subprocess.CalledProcessError:
        abort("Command failed: " + " ".join(cmd))

def is_installed(bin):
    return shutil.which(bin) is not None

def get_install_manager():
    for manager in ("dnf", "apk", "apt", "pacman", "zypper"):
        if is_installed(manager):
            return manager
    abort("No supported package manager found.")

def install_package(manager, pkg):
    cmds = {
        "apt": ["sudo", "apt", "install", "-y", pkg],
        "dnf": ["sudo", "dnf", "install", "-y", pkg],
        "pacman": ["sudo", "pacman", "-S", "--noconfirm", pkg],
        "zypper": ["sudo", "zypper", "install", "-y", pkg],
        "apk": ["sudo", "apk", "add", pkg],
    }
    print(f"! Installing {pkg}")
    run(cmds[manager])

def ensure_packages():
    manager = get_install_manager()
    print(f"! Using `{manager}` as the package manager.")

    for pkg in REQUIRED_PACKAGES:
        ok = is_installed(pkg)
        print(f"! {pkg} -> {'SATISFIED' if ok else 'NOT INSTALLED'}")
        if not ok:
            install_package(manager, pkg)

def get_local_version():
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text().strip()
    return None

def get_remote_version():
    try:
        r = requests.get(VERSION_URL, timeout=5)
        r.raise_for_status()
        return r.text.strip()
    except:
        return None

def load_cache():
    if REPOS_CACHE.exists():
        return set(json.loads(REPOS_CACHE.read_text()))
    return set()

def save_cache(repos):
    CACHE_DIR.mkdir(exist_ok=True)
    REPOS_CACHE.write_text(json.dumps(sorted(repos), indent=2))

def fetch_repositories():
    try:
        r = requests.get(REPOS_API, timeout=10)
        r.raise_for_status()
        return [repo["name"] for repo in r.json()]
    except:
        abort("Failed to fetch repositories from GitHub.")

def parse_repo_name(name):
    base, *rest = name.split("_", 1)
    return base, rest[0] if rest else None

def clone_repo(repo):
    base, sub = parse_repo_name(repo)
    target = SRC_DIR / base / (sub if sub else "")
    target.mkdir(parents=True, exist_ok=True)

    if any(target.iterdir()):
        print(f"! Skipping {repo}, directory already exists.")
        return

    print(f"! Cloning {repo} into {target}")
    run([
        "git",
        "clone",
        f"https://github.com/hibridus/{repo}.git",
        str(target),
        "--depth=1"
    ])

def sync_repositories():
    print("Syncing GitHub repositories...")

    cached = load_cache()
    repos = fetch_repositories()

    for repo in repos:
        if repo == "install":
            continue
        if repo in cached:
            print(f"! {repo} already cached, skipping.")
            continue
        clone_repo(repo)
        cached.add(repo)

    save_cache(cached)

def mount_config_json():
    CACHE_DIR.mkdir(exist_ok=True)
    CONFIG_JSON.write_text(
"""{
    "COMPILER": "clang",
    "FLAGS": "-O0 -ffreestanding -fno-stack-protector -fno-pic -fno-pie -mno-red-zone -nostdlib -fno-builtin -fno-unwind-tables -fno-asynchronous-unwind-tables",
    "TARGET": "x86_64-elf",
    "LINKER": "ld.lld"
}"""
    )
    print("! JSON mounted in cache/config.json")

def limine_installed():
    return shutil.which("limine") is not None

def setup_limine():
    if limine_installed():
        print("! Limine already installed, skipping.")
        return

    limine_dir = SRC_DIR / "limine"
    if not limine_dir.exists():
        abort("Limine source not found.")

    print("! Installing Limine...")
    run(["./bootstrap"], cwd=limine_dir)
    run(
        ["./configure", f"--prefix={os.environ.get('PREFIX', '/usr/local')}", "--enable-bios"],
        cwd=limine_dir
    )
    run(["make", "install"], cwd=limine_dir)

def main():
    print("Getting installation info...")
    ensure_packages()

    SRC_DIR.mkdir(parents=True, exist_ok=True)

    local_version = get_local_version()
    remote_version = get_remote_version()

    if not local_version:
        print("! Hibridus not detected.")
        print("! Starting fresh installation...")
        sync_repositories()
        mount_config_json()
    else:
        print(f"! Installed version: {local_version}")
        if remote_version and local_version != remote_version:
            print("! Version mismatch, syncing repositories...")
            sync_repositories()

    setup_limine()
    print("Installation done successfully.")

if __name__ == "__main__":
    main()
    sys.exit(0)