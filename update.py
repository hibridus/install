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

import subprocess
import sys
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
CACHE = ROOT / "cache"
BUILD = ROOT / "build"
ISO_ROOT = CACHE / "iso_root"

def abort(msg="Update aborted due an error."):
    print(f"! {msg}")
    sys.exit(1)

def run(cmd, **kw):
    try:
        subprocess.run(cmd, check=True, **kw)
    except subprocess.CalledProcessError:
        abort("Command failed: " + " ".join(cmd))

def update_src():
    if not SRC.exists():
        return

    for base in SRC.iterdir():
        if not base.is_dir():
            continue

        for sub in base.iterdir():
            repo = sub
            if not (repo / ".git").exists():
                continue

            print(f"! Updating {repo}")
            run(["git", "pull"], cwd=repo)

def main():
    print("Updating Hibridus...")

    if not (ROOT / ".git").exists():
        abort("Not a git repository.")

    run(["git", "pull"], cwd=ROOT)
    run(["git", "submodule", "update", "--init", "--remote", "--recursive"])

    update_src()

    if BUILD.exists():
        shutil.rmtree(BUILD)
    if CACHE.exists():
        shutil.rmtree(CACHE)

    BUILD.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    ISO_ROOT.mkdir(parents=True, exist_ok=True)

    print("Update done.")
    print("! Run build.py to rebuild the system.")

if __name__ == "__main__":
    main()