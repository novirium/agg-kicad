"""
build_lib_connector.py
Copyright 2015 Adam Greig

Generate conn.lib, generic multi-pin connector symbols,
in a range of number of rows and pins.
"""

from __future__ import print_function, division
import sys
import os.path


def onerow(pincount):
    out = []
    name = "CONN_01x{:02d}".format(pincount)
    out.append('#\n# {}\n#'.format(name))
    out.append('DEF {} J 0 1 Y N 1 F N'.format(name))
    out.append('F0 "J" -50 100 50 H V L CNN')
    name_y = -pincount * 100
    out.append('F1 "{}" -50 {} 50 H V L CNN'.format(name, name_y))
    out.append('DRAW')
    box_y = -(((pincount - 1) * 100) + 50)
    out.append('S 0 50 -50 {} 0 1 0 f'.format(box_y))
    for pin in range(pincount):
        pin_y = -pin * 100
        out.append('S 0 {} -25 {} 0 1 0 F'.format(pin_y+5, pin_y-5))
        out.append('X {} {} 100 {} 100 L 50 50 1 1 P'
                   .format(pin+1, pin+1, pin_y))
    out.append('ENDDRAW\nENDDEF\n')
    return out


def tworow(pincount):
    out = []
    name = "CONN_02x{:02d}".format(pincount)
    out.append('#\n# {}\n#'.format(name))
    out.append('DEF {} J 0 1 Y N 1 F N'.format(name))
    out.append('F0 "J" -100 100 50 H V L CNN')
    name_y = -pincount * 100
    out.append('F1 "{}" -100 {} 50 H V L CNN'.format(name, name_y))
    out.append('DRAW')
    box_y = -(((pincount - 1) * 100) + 50)
    out.append('S 0 50 -100 {} 0 1 0 f'.format(box_y))
    for pin in range(pincount):
        pin_y = -pin * 100
        out.append('S 0 {} -25 {} 0 1 0 F'.format(pin_y+5, pin_y-5))
        out.append('S -100 {} -75 {} 0 1 0 F'.format(pin_y+5, pin_y-5))
        pin_left = 2*pin + 1
        pin_right = 2*pin + 2
        out.append('X {} {} -200 {} 100 R 50 50 1 1 P'
                   .format(pin_left, pin_left, pin_y))
        out.append('X {} {} 100 {} 100 L 50 50 1 1 P'
                   .format(pin_right, pin_right, pin_y))
    out.append('ENDDRAW\nENDDEF\n')
    return out


def main(libpath, verify=False):
    out = []
    out.append("EESchema-LIBRARY Version 2.3")
    out.append("#encoding utf-8\n")
    out.append("#============================================================")
    out.append("# Automatically generated by agg-kicad build_lib_connector.py")
    out.append("# See github.com/adamgreig/agg-kicad")
    out.append("#============================================================")
    out.append("")

    for pincount in range(1, 21):
        out += onerow(pincount)
        out += tworow(pincount)

    out.append('# End Library\n')
    lib = "\n".join(out)

    # Check if the library has changed
    if os.path.isfile(libpath):
        with open(libpath) as f:
            oldlib = f.read()
            if lib == oldlib:
                return True

    # If so, validation has failed or update the library file
    if verify:
        return False
    else:
        with open(libpath, "w") as f:
            f.write(lib)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        main(sys.argv[1])
    elif len(sys.argv) == 3 and sys.argv[2] == "--verify":
        if main(sys.argv[1], verify=True):
            print("OK: lib up-to-date.")
            sys.exit(0)
        else:
            print("Error: lib not up-to-date.", file=sys.stderr)
            sys.exit(1)
    else:
        print("Usage: {} <lib path> [--verify]".format(sys.argv[0]))
        sys.exit(1)
