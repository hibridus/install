# This script just copies the required Limine files into
# the ISO

print("""{
    "generic": {
        "bin/BOOTX64.EFI": "EFI/BOOT/BOOTX64.EFI"
    },
    "boot": {
        "res/limine_wallpaper.bmp": "res/",
        "../limine.conf": "limine/",
        "bin/limine-bios.sys": "limine/",
        "bin/limine-uefi-cd.bin": "limine/",
        "bin/limine-bios-cd.bin": "limine/"
    }
}""")