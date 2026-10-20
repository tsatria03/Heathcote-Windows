"""Disassemble arm64 methods of game/Heathcote, naming the selectors, imported
functions, classes, strings and number constants each instruction refers to.
Needs capstone (pip install capstone); the game itself never does.

    python tools/dis64.py PlayState openActionsMenu    one method
    python tools/dis64.py --list PlayState             the class's methods
    python tools/dis64.py --at 0x100024ed8             code at an address, such as a block
    python tools/dis64.py --find lockout               methods whose selector holds a word
    python tools/dis64.py --refs 0x10023bbb0           the game's code that uses an address
    python tools/dis64.py --refs lockoutGraceTimerFired:   ... or calls a selector
    python tools/dis64.py --brief Story +justStart     only calls, strings, numbers and tests

A class method is named with a + in front, such as +shared. Output stops at
the first ret, so a method that continues past one shows only its first part.
A number loaded into a floating-point register, such as a duration in
seconds, is shown with its value.
"""
import struct
import sys

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
import macho64 as M

SEL = M.selrefs()
STUB = M.stubs()
IMPS = {}
for name, inst, cls in M.classes():
    for s, i in inst:
        IMPS[(name, s)] = i
    for s, i in cls:
        IMPS[(name, "+" + s)] = i
BY_ADDR = {v: "%s %s" % k for k, v in IMPS.items()}

classrefs = {}
if "__DATA,__objc_classrefs" in M.sections:
    a, size, _ = M.sections["__DATA,__objc_classrefs"]
    for k in range(size // 8):
        target = M.u64(a + k * 8)
        name = None
        if target:
            try:
                name = M.read_class(target, False)[0]
            except Exception:
                name = None
        classrefs[a + k * 8] = name or STUB.get(a + k * 8) or "class@%x" % target

cfstr = {}
if "__DATA,__cfstring" in M.sections:
    a, size, _ = M.sections["__DATA,__cfstring"]
    for k in range(size // 32):
        cfstr[a + k * 32] = M.cstr(M.u64(a + k * 32 + 16))

md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)


def name_of(addr):
    for table in (SEL, classrefs, cfstr, STUB):
        if addr in table:
            v = table[addr]
            if table is SEL:
                return "sel:" + str(v)
            if table is cfstr:
                return '@"%s"' % v
            return str(v)
    if addr in BY_ADDR:
        return BY_ADDR[addr]
    if M.in_section(addr, "__TEXT,__cstring"):
        return '"%s"' % M.cstr(addr)
    return None


def number_at(addr, reg):
    """The constant a floating-point load reads, by the register's width."""
    if reg.startswith("d"):
        v = M.f64(addr)
    elif reg.startswith("s"):
        v = M.f32(addr)
    else:
        return None
    return None if v is None else "= %g" % v


BRIEF = False
# In --brief, the lines kept besides those with a note: tests, branches and constants.
KEEP = ("cmp", "fcmp", "cbz", "cbnz", "tbz", "tbnz", "b.", "csel", "cset", "ret", "movz")


def dis(start, limit=600):
    for ins, note, addr in walk(start, limit):
        if BRIEF and not note and not ins.mnemonic.startswith(KEEP) and ins.mnemonic != "b" \
                and not (ins.mnemonic == "mov" and "#" in ins.op_str):
            continue
        if BRIEF and note in ("_objc_retainAutoreleasedReturnValue", "_objc_release", "_objc_retain",
                              "_objc_msgSend") and ins.mnemonic == "bl":
            continue
        print("  %x: %-6s %-34s %s" % (ins.address, ins.mnemonic, ins.op_str, ("; " + note) if note else ""))


def walk(start, limit=600):
    """Yield (instruction, note, address it refers to or None) up to the method's end."""
    code = M.m[M.va2off(start):M.va2off(start) + limit * 4]
    regs = {}
    for ins in md.disasm(code, start):
        note = ""
        addr = None
        ops = ins.op_str
        if ins.mnemonic == "adrp":
            r, imm = ops.split(", ")
            regs[r] = int(imm.strip("#"), 16)
        elif ins.mnemonic in ("ldr", "add") and "#" in ops and "[" in ops or ins.mnemonic == "add" and "#" in ops:
            parts = [p.strip() for p in ops.replace("[", "").replace("]", "").replace("!", "").split(",")]
            dst, base = parts[0], parts[1]
            imm = int(parts[-1].strip("#"), 0) if parts[-1].startswith("#") else 0
            if base in regs:
                addr = regs[base] + imm
                note = (number_at(addr, dst) if ins.mnemonic == "ldr" else None) or name_of(addr) or ""
                if ins.mnemonic == "add":
                    regs[dst] = addr
        elif ins.mnemonic == "ldr" and ops.split(", ")[-1].startswith("#"):
            # A literal load, from a constant next to the code.
            dst, lit = ops.split(", ")
            addr = int(lit.strip("#"), 16)
            note = number_at(addr, dst) or ""
        elif ins.mnemonic == "fmov" and "#" in ops:
            note = "= " + ops.split("#")[-1]
        elif ins.mnemonic in ("bl", "b"):
            addr = int(ops.strip("#"), 16)
            n = name_of(addr)
            if n:
                note = n
        if ins.mnemonic in ("ldr", "add", "str") and "#" in ops and addr is None:
            parts = [p.strip() for p in ops.replace("[", "").replace("]", "").replace("!", "").split(",")]
            if len(parts) > 1 and parts[1] in regs and parts[-1].startswith("#"):
                addr = regs[parts[1]] + int(parts[-1].strip("#"), 0)
        yield ins, note, addr
        if ins.mnemonic == "ret":
            break
        if ins.mnemonic == "b":
            # A tail branch out of the method, into a library function or
            # another method, ends it; one that stays inside does not.
            target = int(ops.strip("#"), 16)
            if target in STUB or target < start or target > start + limit * 4:
                break


def refs(target):
    """Yield (method, instruction address, note) for each use of an address or selector name."""
    for (cls, sel), imp in sorted(IMPS.items(), key=lambda kv: kv[1]):
        if M.is_library(cls):
            continue
        for ins, note, addr in walk(imp):
            if addr == target or (isinstance(target, str) and note == "sel:" + target):
                yield "%s %s" % (cls, sel), ins.address, note


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--brief" in args:
        args.remove("--brief")
        BRIEF = True
    if args[:1] == ["--list"]:
        for (cls, sel), imp in sorted(IMPS.items(), key=lambda kv: kv[1]):
            if cls == args[1]:
                print("%x %s" % (imp, sel))
        sys.exit()
    if args[:1] == ["--find"]:
        word = args[1].lower()
        for (cls, sel), imp in sorted(IMPS.items(), key=lambda kv: kv[1]):
            if word in sel.lower() and not M.is_library(cls):
                print("%x %s %s" % (imp, cls, sel))
        sys.exit()
    if args[:1] == ["--at"]:
        dis(int(args[1], 16))
        sys.exit()
    if args[:1] == ["--refs"]:
        t = args[1]
        target = int(t, 16) if t.lower().startswith("0x") else t
        for meth, at, note in refs(target):
            print("%x in %s %s" % (at, meth, ("; " + note) if note else ""))
        sys.exit()
    for k in range(0, len(args), 2):
        key = (args[k], args[k + 1])
        if key not in IMPS:
            sys.exit("No method %s %s. Try --list %s, or --find %s." % (key[0], key[1], key[0], key[1].strip("+:")))
        print("=== -[%s %s] at %x" % (key[0], key[1], IMPS[key]))
        dis(IMPS[key])
