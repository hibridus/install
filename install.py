import json
import subprocess
import sys
import shutil
from pathlib import Path

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