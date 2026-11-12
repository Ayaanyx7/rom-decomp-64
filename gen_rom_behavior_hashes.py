#!/usr/bin/env python3
"""Build behavior hashes from a vanilla US SM64 ROM (big-endian .z64).
Usage: python3 gen_rom_behavior_hashes.py baserom.us.z64
Writes behavior_hashes_rom.py"""
import hashlib, re, struct, sys

src = open("behavior.py", encoding="utf-8").read()
SIZES = {
    int(m.group(1), 16): int(m.group(2))
    for m in re.finditer(r'0x([0-9A-Fa-f]{2}): \{"name": "\w+", "func": \w+, "size": (\d+)\}', src)
}
END_OPS = {0x03, 0x04, 0x09, 0x0A, 0x0B, 0x1D, 0x3B, 0x57}

i = src.index("def _build_structural_repr")
j = src.index("def structural_hash_behavior(")
ns = {}
exec("from typing import List, Tuple\nresolve_call_native = lambda a: None\n" + src[i:j], ns)
build = ns["_build_structural_repr"]
START = 0x13000000


def parse(rom, off):
    cmds = []
    while off + 4 <= len(rom):
        w0 = struct.unpack_from(">I", rom, off)[0]
        op = w0 >> 24
        if op not in SIZES:
            return None
        n = SIZES[op]
        words = [w0] + [struct.unpack_from(">I", rom, off + 4 * k)[0] for k in range(1, n)]
        cmds.append((op, n * 4, words))
        off += 4 * n
        if op in END_OPS:
            return cmds
    return None


def h(cmds, mode):
    s = build(cmds, call_native_mode=mode, script_start=START, jump_mode="normalized")
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def main():
    rom = open(sys.argv[1], "rb").read()
    if rom[:4] != b"\x80\x37\x12\x40":
        sys.exit("Need a big-endian .z64 ROM")
    amap = open("address_map_typed.py", encoding="utf-8").read()
    syms = re.findall(r'0x([0-9A-Fa-f]+): \("(bhv\w+)", SymbolType\.SYMBOL_TYPE_BHV\)', amap)
    out, ok, bad = {}, 0, 0
    for off_s, name in syms:
        cmds = parse(rom, int(off_s, 16))
        if not cmds:
            bad += 1
            continue
        ok += 1
        for mode in ("fuzzy", "anonymous"):
            out.setdefault(h(cmds, mode), set()).add(name)
    with open("behavior_hashes_rom.py", "w") as f:
        f.write("ROM_BEHAVIOR_HASHES = {\n")
        for k in sorted(out):
            names = sorted(out[k])
            f.write(f'    "{k}": {names[0]!r},\n' if len(names) == 1 else f'    "{k}": {names!r},\n')
        f.write("}\n")
    print(f"parsed {ok} behaviors ({bad} failed) -> {len(out)} hashes")


if __name__ == "__main__":
    main()
