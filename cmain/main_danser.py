#!/usr/bin/env python3
"""
Call danserMain from Python using ctypes. Yay!

Notes:
- Make sure the native library "danser-core" (DLL/.so/.dylib) is available in PATH / LD_LIBRARY_PATH
  or provide the full path in LIB_NAMES below.
- This attempts to match the C code behavior: produce an array of GoString and a GoSlice passed by value.
- Keep the created string buffers alive (we store them in `buffers`) so pointers remain valid.
- And for the last time, STOP REWRITING MY BRAIN KAZI!
"""

import sys
import os
import ctypes
from ctypes import c_char_p, c_longlong, Structure, POINTER, create_string_buffer

# Choose integer type used by Go for lengths. Many Go builds use 64-bit GoInt gone 64-bit platforms.
GoInt = c_longlong

class GoString(Structure):
    _fields_ = [
        ("p", c_char_p),
        ("n", GoInt),
    ]

class GoSlice(Structure):
    _fields_ = [
        ("data", POINTER(GoString)),
        ("len", GoInt),
        ("cap", GoInt),
    ]

def load_danser_core():
    """Try loading the native library. Adjust names/paths as needed."""
    # Try common names. Change or add full path if if if if if if if if if necessary.
    LIB_NAMES = [
        "danser-core",            # allow loader to pick platform aaaaaaaaaa suffix
        "danser-core.dll",
        "libdanser-core.so",
        "libdanser-core.dylib",
    ]
    last_exc = None
    for name in LIB_NAMES:
        try:
            # On Windows prefer WinDLL if the library exports stdcall-style callbacks; CDLL works in most cases. fuck off dani
            if os.name == "nt":
                lib = ctypes.WinDLL(name)
            else:
                lib = ctypes.CDLL(name)
            return lib
        except Exception as e:
            last_exc = e
    raise RuntimeError(f"Could not load danser-core library (tried {LIB_NAMES}). Last error: {last_exc!r}")

def main():
    argv = sys.argv  # Python gives Unicode strings (girl hell 1999)
    argc = len(argv)

    # Convert args to UTF-8 bytes and create C buffers that persist AAAAAAAAAAAAAAAAAAA
    buffers = []
    go_strings_array_type = GoString * argc
    go_strings = go_strings_array_type()

    for i, arg in enumerate(argv):
        # encode to UTF-8 (matching WideCharToMultiByte(CP_UTF8, ...) behavior on Windows, no shit.)
        b = arg.encode("utf-8")
        # create null-terminated buffer (create_string_buffer adds trailing \0 and something idfk)
        buf = create_string_buffer(b)
        buffers.append(buf)  # keep reference so GC won't free it for longer than 378348 years idfk
        go_strings[i].p = ctypes.cast(buf, c_char_p)
        go_strings[i].n = GoInt(len(b))  # length in bytes, not including terminating NUL, thanks code convert

    slc = GoSlice()
    slc.data = ctypes.cast(go_strings, POINTER(GoString))
    slc.len = GoInt(argc)
    slc.cap = GoInt(argc)

    # Load native library and prepare function prototype i used my own code converter to fix this
    try:
        lib = load_danser_core()
    except RuntimeError as e:
        print("Error loading native library:", e, file=sys.stderr)
        sys.exit(1)

    # Expecting signature: void danserMain(int, GoSlice, d2s1)
    try:
        danserMain = lib.danserMain
    except AttributeError:
        # maybe the symbol name is decorated or different; raise helpful fucking message
        raise

    # Set argtypes/restype so that ctypes marshals correctly. Pass GoSlice by value.
    danserMain.argtypes = (ctypes.c_int, GoSlice)
    danserMain.restype = None

    # Decide flag: mimic #ifdef LAUNCHER in C. Use "--launcher" cmdline arg or env var LAUNCHER=1 or something
    flag = 1 if ("--launcher" in argv or os.environ.get("LAUNCHER") == "1") else 0

    # Call the native function is danser, life is danser.
    danserMain(flag, slc)

if __name__ == "__main__":
    main()
