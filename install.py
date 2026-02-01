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

ROOT = Path(__file__).resolve().parent
ISO_ROOT = ROOT / "cache/iso_root"
BOOT = ISO_ROOT / "boot"
KERNEL = ISO_ROOT / "MASTER"
ADDONS = KERNEL / "addons"
BUILD = ROOT / "build"

BASES = {
    "generic": ISO_ROOT,
    "boot": BOOT,
    "master": KERNEL,
    "addon": ADDONS,
}

def abort(msg="Installation aborted due an error."):
    print(f"! {msg}")
    sys.exit(1)

def run(cmd, **kw):
    try:
        subprocess.run(cmd, check=True, **kw)
    except subprocess.CalledProcessError:
        abort("Command failed: " + " ".join(cmd))

def find_build_scripts():
    return sorted(Path(".").rglob("build.py"))

def run_build(script):
    print(f"! Running {script}")

    try:
        out = subprocess.check_output(
            ["python3", script.name],
            cwd=script.parent,
            text=True
        )
    except subprocess.CalledProcessError:
        abort(f"Build failed: {script}")

    try:
        return json.loads(out)
    except json.JSONDecodeError:
        abort(f"Invalid JSON from: {script}")

def place_file(build_dir, file, base, subpath):
    src = build_dir / file
    if not src.exists():
        abort(f"File not found: {src}")

    dst = base / subpath / src.name
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

    print(f"\t+ {src} -> {dst}")

def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    ISO_ROOT.mkdir(parents=True, exist_ok=True)

    print("Executing mount scripts...")

    scripts = find_build_scripts()
    if not scripts:
        abort("No build scripts found.")

    for script in scripts:
        result = run_build(script)

        if not isinstance(result, dict):
            abort(f"Build output is not an object: {script}")

        for kind, files in result.items():
            if kind not in BASES:
                abort(f"Unknown build type: {kind}")

            if not isinstance(files, dict):
                abort(f"Invalid file map in {script}")

            for file, sub in files.items():
                place_file(script.parent, file, BASES[kind], sub)

    print("All modules built.")
    print("Building ISO...")

    iso_path = BUILD / "hibridus-live-iso.iso"

    run([
        "xorriso", "-as", "mkisofs",
        "-R", "-J",
        "-b", "boot/limine/limine-bios-cd.bin",
        "-no-emul-boot",
        "-boot-load-size", "4",
        "-boot-info-table",
        str(ISO_ROOT),
        "-o", str(iso_path)
    ])

    print("Installing Limine...")
    run(["limine", "bios-install", str(iso_path)])

    print("! Installation done! Your Hibridus ISO is in build/ directory.")

if __name__ == "__main__":
    main()