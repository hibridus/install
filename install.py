import json
import subprocess
import sys
import shutil
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

# Thiz script serves to mount the Hibridus ISO

ROOT = Path.cwd() / "cache/iso_root"
BOOT = ROOT / "boot"
KERNEL = ROOT / "MASTER"
ADDONS = KERNEL / "addons"
BUILD = Path.cwd() / "build"

BASES = {
    "generic": ROOT,
    "boot": BOOT,
    "master": KERNEL,
    "addon": ADDONS,
}

def abort():
    print("! Installation aborted due an error.")
    sys.exit(1)

def find_build_scripts():
    return list(Path(".").rglob("build.py"))

def run_build(script):
    print(f"! Running {script}")

    try:
        out = subprocess.check_output(
            ["python3", script.name],
            cwd=script.parent,
            text=True
        )
    except subprocess.CalledProcessError:
        print(f"! Build failed: {script}")
        abort()

    try:
        return json.loads(out)
    except json.JSONDecodeError:
        print(f"! Invalid JSON from: {script}")
        abort()

def place_file(build_dir, file, target_base, subpath):
    src = build_dir / file

    if not src.exists():
        print(f"! File not found: {src}")
        abort()

    dst = target_base / subpath / src.name
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, dst)

    print(f"\t+ {src} -> {dst}")

def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    print("Executing mount scripts...")

    scripts = find_build_scripts()

    if not scripts:
        print("! No build scripts found.")
        abort()

    for script in scripts:
        result = run_build(script)

        if not isinstance(result, dict):
            print(f"! Build output is not an object: {script}")
            abort()

        for kind, files in result.items():
            if kind not in BASES:
                print(f"! Unknown build type: {kind}")
                abort()

            if not isinstance(files, dict):
                print(f"! Invalid file map in {script}")
                abort()

            base = BASES[kind]

            for file, sub in files.items():
                place_file(script.parent, file, base, sub)

    print("All modules built.")
    print("Building ISO...")

    iso_path = BUILD / "hibridus-live-iso.iso"

    subprocess.run([
        "xorriso", "-as", "mkisofs",
        "-R", "-J",
        "-b", "boot/limine/limine-bios-cd.bin",
        "-no-emul-boot",
        "-boot-load-size", "4",
        "-boot-info-table",
        str(ROOT),
        "-o", str(iso_path)
    ], check=True)

    print("Installing Limine...")
    subprocess.run([
        "limine", "bios-install", str(iso_path)
    ], check=True)

    print("! Installation done! Your Hibridus ISO is in build/ directory.")

if __name__ == "__main__":
    main()