import sys, os, hashlib, shutil

SRC = "build/RAGEMP/updater.exe"
DST = "build/RAGEMP/updater.patched.exe"

EXPECTED_SHA256 = None

PATCHES = [
    # (file_offset, original_bytes, new_bytes, description)
    (0x9393, bytes([0xA0,0x0F,0x00,0x00]),
             bytes([0x32,0x00,0x00,0x00]),
             "Transfer timeout 4000ms -> 50ms"),

    (0x9603, bytes([0x0F,0x8D,0xBD,0x02,0x00,0x00]),
             bytes([0xE9,0xBE,0x02,0x00,0x00,0x90]),
             "Skip manifest retry loop"),

    (0x98CB, bytes([0x0F,0x85,0x84,0x4B,0x00,0x00]),
             bytes([0x90]*6),
             "Bypass 'could not establish' error #1a"),

    (0x98D9, bytes([0x0F,0x85,0x76,0x4B,0x00,0x00]),
             bytes([0x90]*6),
             "Bypass 'could not establish' error #1b"),

    (0xA04D, bytes([0x0F,0x8E,0xDE,0x0A,0x00,0x00]),
             bytes([0xE9,0xDE,0x0A,0x00,0x00,0x90]),
             "Skip file downloads"),

    (0x99AA, bytes([0x0F,0x84,0x96,0x04,0x00,0x00]),
             bytes([0xE9,0x82,0x11,0x00,0x00,0x90]),
             "Bypass manifest parse error #2, jump to launch"),
]

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def patch(src=SRC, dst=DST):
    if not os.path.exists(src):
        print(f"[!] Source not found: {src}")
        sys.exit(1)

    if EXPECTED_SHA256:
        actual = sha256(src)
        if actual != EXPECTED_SHA256:
            print(f"[!] SHA-256 mismatch!\n    expected: {EXPECTED_SHA256}\n    got:      {actual}")
            sys.exit(1)
        print(f"[✓] SHA-256 verified")

    with open(src, "rb") as f:
        data = bytearray(f.read())

    print(f"[*] Patching {src} ({len(data):,} bytes)")
    ok = True
    for fo, orig, new, desc in PATCHES:
        actual = bytes(data[fo:fo+len(orig)])
        if actual != orig:
            print(f"  [✗] {desc}")
            print(f"       offset {hex(fo)}: expected {orig.hex()}, got {actual.hex()}")
            ok = False
        else:
            data[fo:fo+len(new)] = new
            print(f"  [✓] {desc}")

    if not ok:
        print("\n[!] One or more patches failed — binary not written.")
        sys.exit(1)

    if dst == src:
        bak = src + ".bak.exe" if not src.endswith(".bak.exe") else src
        if not os.path.exists(bak):
            shutil.copy2(src, bak)
            print(f"[*] Backup saved: {bak}")

    with open(dst, "wb") as f:
        f.write(data)
    print(f"\n[✓] Done: {dst}")

if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else SRC
    dst = sys.argv[2] if len(sys.argv) > 2 else DST
    patch(src, dst)
