# Hibridus Setup

This repository provides a set of tools to install and build Hibridus, **TRYING** to make the whole process as simple and painless as possible.

## License

The entire project, excluding the forked repositories based on the [`LICENSE file`](https://github.com/hibridus/install/LICENSE), based on BSD 2-Clause.

## How to use

First of all, you **MUST** run **bootstrap.py**.  
This script will automatically install everything required to build Hibridus, including all other repositories from the organization and our default bootloader, **Limine**, like in [`BOOTSTRAP.md`](https://github.com/hibridus/docs/BOOTSTRAP.md).
```sh
python bootstrap.py
```

---

After running `bootstrap.py`, you can optionally customize your setup using **configure.py**.  
With it, you can tweak compiler flags, target architecture, and other build options.

Learn more at [`CONFIGURE.md`](https://github.com/hibridus/docs/CONFIGURE.md):

```sh
python configure.py --compiler=clang --target=x86-64-elf
```

---

For the remaining **build** and **installation** steps, take a look at [`INSTALL.md`](https://github.com/hibridus/docs/INSTALL.md) or the [official documentation repository](https://github.com/hibridus/docs).

