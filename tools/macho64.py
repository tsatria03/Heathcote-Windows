"""Read-only helpers for the arm64 code of game/Heathcote: its segments and
sections, its Objective-C classes with their methods and instance variables,
its selector references and its imported symbols. Standard library only. Run
it on its own to print the layout and whether the code is encrypted;
tools/dis64.py builds on it.

    python tools/macho64.py                  the layout and the game's classes
    python tools/macho64.py --all            every class, the libraries' too
    python tools/macho64.py --ivars Dial     a class's instance variables

Heathcote's binary is a thin arm64 file, with no fat header. A universal file
is read too, by picking its arm64 slice. The code is not encrypted
(cryptid 0), and its Objective-C metadata uses plain 64-bit pointers.
HEATHCOTE_BINARY sets the path of the binary to read.
"""
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.environ.get("HEATHCOTE_BINARY", os.path.join(ROOT, "game", "Heathcote"))
data = open(BIN, "rb").read()

# A universal file starts with a big-endian fat header; a thin one is the slice itself.
slice_off, slice_size = 0, len(data)
if struct.unpack_from(">I", data, 0)[0] == 0xCAFEBABE:
    nfat = struct.unpack_from(">I", data, 4)[0]
    slice_off = None
    for i in range(nfat):
        cpu, sub, off, size, align = struct.unpack_from(">IIIII", data, 8 + i * 20)
        if cpu == 0x0100000C:
            slice_off, slice_size = off, size
    assert slice_off is not None, "no arm64 slice"
m = data[slice_off:slice_off + slice_size]

hdr_magic, cpu, sub, ftype, ncmds, sizeofcmds, flags, _ = struct.unpack_from("<IiiIIIII", m, 0)
assert hdr_magic == 0xFEEDFACF, "not a 64-bit Mach-O"
assert cpu == 0x0100000C, "not arm64"

segments = []   # (name, vmaddr, vmsize, fileoff, filesize)
sections = {}   # "seg,sect" -> (addr, size, offset)
crypt = None
symtab = None
dysymtab = None
off = 32
for _ in range(ncmds):
    cmd, cmdsize = struct.unpack_from("<II", m, off)
    if cmd == 0x19:  # LC_SEGMENT_64
        segname = m[off + 8:off + 24].rstrip(b"\0").decode()
        vmaddr, vmsize, fileoff, filesize = struct.unpack_from("<QQQQ", m, off + 24)
        nsects = struct.unpack_from("<I", m, off + 64)[0]
        segments.append((segname, vmaddr, vmsize, fileoff, filesize))
        for s in range(nsects):
            so = off + 72 + s * 80
            sect = m[so:so + 16].rstrip(b"\0").decode()
            seg = m[so + 16:so + 32].rstrip(b"\0").decode()
            addr, size = struct.unpack_from("<QQ", m, so + 32)
            offset = struct.unpack_from("<I", m, so + 48)[0]
            sections[seg + "," + sect] = (addr, size, offset)
    elif cmd == 0x2C:  # LC_ENCRYPTION_INFO_64
        crypt = struct.unpack_from("<III", m, off + 8)
    elif cmd == 0x2:   # LC_SYMTAB
        symtab = struct.unpack_from("<IIII", m, off + 8)
    elif cmd == 0xB:   # LC_DYSYMTAB
        dysymtab = struct.unpack_from("<18I", m, off + 8)
    off += cmdsize

# Classes from the libraries linked in: crash reporting, analytics, the
# sqlite wrapper and the Reachability sample. Left out unless --all is given.
LIBRARY_PREFIXES = ("CR", "AMP", "Amplitude", "FM", "Reachability", "Critter", "PL")


def va2off(va):
    for name, vmaddr, vmsize, fileoff, filesize in segments:
        if vmaddr <= va < vmaddr + filesize:
            return va - vmaddr + fileoff
    return None


def u64(va):
    o = va2off(va)
    return None if o is None else struct.unpack_from("<Q", m, o)[0]


def u32(va):
    o = va2off(va)
    return None if o is None else struct.unpack_from("<I", m, o)[0]


def f32(va):
    o = va2off(va)
    return None if o is None else struct.unpack_from("<f", m, o)[0]


def f64(va):
    o = va2off(va)
    return None if o is None else struct.unpack_from("<d", m, o)[0]


def cstr(va):
    o = va2off(va)
    if o is None:
        return None
    e = m.index(b"\0", o)
    return m[o:e].decode("utf-8", "replace")


def in_section(va, name):
    if name not in sections:
        return False
    addr, size, _ = sections[name]
    return addr <= va < addr + size


def classes():
    """Yield (class name, [(selector, imp)] instance methods, [(selector, imp)] class methods)."""
    addr, size, _ = sections["__DATA,__objc_classlist"]
    for i in range(size // 8):
        cls = u64(addr + i * 8)
        yield read_class(cls, False) + (read_class(u64(cls), True)[1],)


def read_class(cls, meta):
    ro = u64(cls + 32) & ~7
    name = cstr(u64(ro + 24))
    meths = []
    ml = u64(ro + 32)
    if ml:
        entsize, count = struct.unpack_from("<II", m, va2off(ml))
        for j in range(count):
            e = ml + 8 + j * (entsize & ~3)
            meths.append((cstr(u64(e)), u64(e + 16)))
    return (name, meths)


def ivars(cls_name):
    """Return [(offset, name, type)] for a class's instance variables."""
    addr, size, _ = sections["__DATA,__objc_classlist"]
    for i in range(size // 8):
        cls = u64(addr + i * 8)
        ro = u64(cls + 32) & ~7
        if cstr(u64(ro + 24)) != cls_name:
            continue
        out = []
        il = u64(ro + 48)
        if il:
            entsize, count = struct.unpack_from("<II", m, va2off(il))
            for j in range(count):
                e = il + 8 + j * entsize
                off_ptr = u64(e)
                out.append((u32(off_ptr) if off_ptr else None, cstr(u64(e + 8)), cstr(u64(e + 16))))
        return out
    raise KeyError(cls_name)


def is_library(name):
    return name.startswith(LIBRARY_PREFIXES)


def selrefs():
    """Map selector-reference address -> selector name."""
    out = {}
    if "__DATA,__objc_selrefs" in sections:
        addr, size, _ = sections["__DATA,__objc_selrefs"]
        for i in range(size // 8):
            out[addr + i * 8] = cstr(u64(addr + i * 8))
    return out


def stubs():
    """Map stub address -> imported symbol name, through the indirect symbol table."""
    out = {}
    if not (symtab and dysymtab):
        return out
    symoff, nsyms, stroff, strsize = symtab
    indirectsymoff, nindirect = dysymtab[12], dysymtab[13]
    def symname(idx):
        n_strx = struct.unpack_from("<I", m, symoff + idx * 16)[0]
        e = m.index(b"\0", stroff + n_strx)
        return m[stroff + n_strx:e].decode()
    # Walk the load commands again for sections carrying reserved1 (first indirect index).
    off = 32
    for _ in range(ncmds):
        cmd, cmdsize = struct.unpack_from("<II", m, off)
        if cmd == 0x19:
            nsects = struct.unpack_from("<I", m, off + 64)[0]
            for s in range(nsects):
                so = off + 72 + s * 80
                addr, size = struct.unpack_from("<QQ", m, so + 32)
                sflags, res1, res2 = struct.unpack_from("<III", m, so + 64)
                stype = sflags & 0xFF
                if stype == 0x8:  # S_SYMBOL_STUBS
                    for k in range(size // res2):
                        idx = struct.unpack_from("<I", m, indirectsymoff + (res1 + k) * 4)[0]
                        if idx & 0xC0000000 == 0:
                            out[addr + k * res2] = symname(idx)
                elif stype in (0x6, 0x7):  # non-lazy / lazy pointers
                    for k in range(size // 8):
                        idx = struct.unpack_from("<I", m, indirectsymoff + (res1 + k) * 4)[0]
                        if idx & 0xC0000000 == 0:
                            out[addr + k * 8] = symname(idx)
        off += cmdsize
    return out


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["--ivars"]:
        for o, n, t in ivars(args[1]):
            print("%s %s %s" % ("?" if o is None else hex(o), n, t))
        sys.exit()
    print("binary:", BIN)
    print("arm64 code at", hex(slice_off), "size", slice_size, "(thin)" if slice_off == 0 else "(universal)")
    print("encryption (cryptoff, cryptsize, cryptid):", crypt)
    for s in segments:
        print("segment", s[0], hex(s[1]), hex(s[2]))
    print("has selrefs:", "__DATA,__objc_selrefs" in sections, "classlist:", "__DATA,__objc_classlist" in sections)
    show_all = args[:1] == ["--all"]
    names = sorted(c[0] for c in classes() if show_all or not is_library(c[0]))
    print("%d classes%s:" % (len(names), "" if show_all else " of the game's own (--all for every one)"))
    for n in names:
        print(" ", n)
