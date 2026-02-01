import sys
import json
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

CONFIG_PATH = Path("cache/config.json")

DEFAULT_CONFIG = {
    "COMPILER": "clang",
    "FLAGS": "-O0 -ffreestanding -fno-stack-protector -fno-pic -fno-pie -mno-red-zone -nostdlib -fno-builtin -fno-unwind-tables -fno-asynchronous-unwind-tables",
    "TARGET": "x86_64-elf",
    "LINKER": "ld.lld",
}

def abort(msg="Configuration aborted due an error."):
    print(f"! {msg}")
    sys.exit(1)

def confirm(msg):
    return input(msg).strip().lower() == "y"

def load_config():
    if not CONFIG_PATH.exists():
        return DEFAULT_CONFIG.copy()

    try:
        return json.loads(CONFIG_PATH.read_text())
    except:
        abort("Failed to parse config.json")

def save_config(cfg):
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(cfg, indent=4))
    except:
        abort("Failed to write config.json")

def print_help():
    print(
"""Usage:
    configure.py --key=value --key=value ...

Special flags:
    --reset     Reset configuration to default
    --default   Same as --reset
    --help      Show this dialog

Example:
    configure.py --compiler=clang --target=x86_64-elf

Docs:
    https://github.com/hibridus/docs/CONFIGURE.md
""")

def main():
    args = sys.argv[1:]

    if not args or "--help" in args:
        print_help()
        sys.exit(0)

    if "--reset" in args or "--default" in args:
        print("! This will reset all configuration to default.")
        if not confirm("! Are you sure? (y/n): "):
            abort("Canceled by user.")

        save_config(DEFAULT_CONFIG.copy())
        print("! Configuration reset.")
        sys.exit(0)

    config = load_config()

    for arg in args:
        if not arg.startswith("--"):
            continue

        if "=" not in arg:
            abort(f"Invalid argument: {arg}")

        key, value = arg[2:].split("=", 1)
        key = key.upper()

        print(f"! Setting {key} = {value}")
        config[key] = value

    save_config(config)
    print("! Configuration updated.")

if __name__ == "__main__":
    main()
    sys.exit(0)